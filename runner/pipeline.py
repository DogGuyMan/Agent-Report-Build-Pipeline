#!/usr/bin/env python3
"""세 실행기가 함께 쓰는 단계 기계. 갈래 · 단계 · 전이표 · 그래프 · 드라이버.

**`machine/` 을 import 하지 않는다.** 여기를 import 하는 것만으로 해석기가 바뀌거나
무거운 라이브러리가 실리면 안 된다 — `test_import_isolation.py` 가 그것을 잰다.

**`Any` 를 쓰지 않는다.** 바깥이 꼴을 정하는 JSON 은 `TypedDict` 로 선언하고 `msgspec` 이
`load` 에서 검증한다. 안 맞으면 예외이고, `Pipeline.run` 이 그것을 `FAIL` 로 바꾼다.
"""
import os
import re
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import ClassVar, Generic, TypeVar, cast

import jinja2
import jinja2.meta
import jinja2.nodes
import msgspec

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from tools.template import TemplateError  # noqa: E402
import measure as M  # noqa: E402
from measure import AgentResult, StageRow  # noqa: E402

# ── 1. 갈래 넷 — 비트 하나씩. 늘리지 않는다 ─────────────────────────────
OK = 1
FAIL = 2
SKIP = 4
GATE = 8

KINDS = (OK, FAIL, SKIP, GATE)
KIND_NAME = {OK: "OK", FAIL: "FAIL", SKIP: "SKIP", GATE: "GATE"}

# 전이의 목적지 특수값. 단계 이름과 겹치지 않도록 널 문자로 시작한다.
HALT = "\x00halt"
NEXT = "\x00next"


def _no_rows() -> list[StageRow]:
    """`field(default_factory=list)` 는 원소 형을 잃는다. 형이 붙은 빈 목록을 낸다."""
    return []


@dataclass
class Outcome:
    """`perform()` 이 낸 것. 갈래는 정확히 하나이고, 세션 N개면 행도 N개다."""
    kind: int
    why: str = ""
    rows: list[StageRow] = field(default_factory=_no_rows)


@dataclass
class RunContext:
    """세 모드가 공유하는 칸만. 모드마다 이것을 상속해 자기 칸을 더한다."""
    root: str
    model: str
    timeout: float | None = None
    concurrency: int = 8


C = TypeVar("C", bound=RunContext)


@dataclass(frozen=True)
class Artifact(Generic[C]):
    """단계가 읽고 쓰는 파일 하나. 자리는 `ctx` 가 정하므로 경로를 박지 않는다.

    둘 다 `None` 이면 있는지만 본다 — `data.ts` 처럼 JSON 이 아닌 것과, 선언이 실물과
    어긋나 형으로 못 보는 것이다. `schema` 는 **꼴**(msgspec 이 본다), `check` 는 꼴이 맞은
    뒤의 **뜻**(문항 수 · 정답 자리처럼 형으로 못 적는 규칙)이다. 꼴이 틀리면 뜻은 보지 않는다.
    """
    name: str
    locate: Callable[[C], str]
    schema: type[object] | None = None
    check: Callable[[object], list[str]] | None = None


T = TypeVar("T")


def load(path: str, t: type[T]) -> T:
    """JSON 파일을 형 `t` 로 읽는다. 없거나 깨졌거나 꼴이 틀리면 예외다 — 여기서 잡지 않는다."""
    with open(path, "rb") as f:
        return msgspec.json.decode(f.read(), type=t)


def check_file(path: str, schema: type[object] | None,
               check: Callable[[object], list[str]] | None = None) -> list[str]:
    """꼴을 먼저, 통과하면 뜻을 본다. 불평 목록을 낸다. 산출물 경계에서만 쓴다."""
    try:
        obj = load(path, schema or object)
    except msgspec.DecodeError as e:
        return [str(e)]
    return check(obj) if check is not None else []


# ── 2. 단계 — 상태를 갖지 않는다. 갈래는 반환값이다 ─────────────────────
class Stage(ABC, Generic[C]):
    """단계 하나. `emits` 는 **선언**이고 실제로 난 갈래는 `perform` 이 반환한다.

    `emits` 를 클래스에 두는 덕에 **시작 전에** 전이표 완결성을 검사할 수 있다.
    같은 단계를 층마다 다시 돌아도 인스턴스에 남는 것이 없다.
    """
    name: str = ""
    emits: int = OK | FAIL

    def reads(self, ctx: C) -> list[Artifact[C]]:
        """돌기 전에 있어야 하는 것. 없으면 단계를 돌리지 않는다.

        **없어도 정상인 선택 입력은 여기 넣지 않는다.** 시뮬레이터가 잡을 결함이
        없기 때문이다 — 그런 것은 단계 안에서 존재를 본다.
        """
        return []

    def writes(self, ctx: C) -> list[Artifact[C]]:
        """**돌고 나면 있어야 하는 것.** 꼴이 어긋나면 `FAIL` 이 된다.

        이 단계의 파이썬 코드가 쓴다는 뜻이 아니다 — LLM 자식 프로세스가 쓰는 것도
        여기 선다. 누가 썼는지가 아니라 무엇이 있어야 하는지의 선언이다.
        """
        return []

    @abstractmethod
    def perform(self, ctx: C) -> Outcome:
        ...


def missing_reads(stage: Stage[C], ctx: C) -> list[str]:
    """읽을 산출물 중 없거나 꼴이 어긋난 것의 불평 목록."""
    out: list[str] = []
    for art in stage.reads(ctx):
        path = art.locate(ctx)
        if not os.path.exists(path):
            out.append("읽을 것이 없다 — %s" % art.name)
            continue
        if art.schema is not None or art.check is not None:
            out.extend("%s — %s" % (art.name, c) for c in check_file(path, art.schema, art.check))
    return out


def bad_writes(stage: Stage[C], ctx: C) -> list[str]:
    """쓴 산출물 중 안 나왔거나 꼴이 어긋난 것의 불평 목록."""
    out: list[str] = []
    for art in stage.writes(ctx):
        path = art.locate(ctx)
        if not os.path.exists(path):
            out.append("%s — 나오지 않았다" % art.name)
            continue
        if art.schema is not None or art.check is not None:
            out.extend("%s — %s" % (art.name, c) for c in check_file(path, art.schema, art.check))
    return out


# ── 3. 전이표 — 파이프라인 밖에 하나. 단계는 자기 다음을 모른다 ──────────
class Edges:
    """`(단계 이름, 갈래) -> 목적지`. 목적지는 단계 이름이거나 `HALT` · `NEXT` 다.

    단계 이름 `"*"` 는 모든 단계에 걸리는 기본 규칙이다. 단계별 규칙이 먼저다.
    **기본값을 코드에 숨기지 않는다** — 규칙이 없으면 `None` 을 내고,
    그것을 `simulate` 가 완결성 위반으로 잡는다.
    """

    def __init__(self, table: Mapping[tuple[str, int], str]) -> None:
        self._table = dict(table)

    def dest(self, stage: str, kind: int) -> str | None:
        if (stage, kind) in self._table:
            return self._table[(stage, kind)]
        return self._table.get(("*", kind))


# ── 4. 그래프 — 팩토리가 미리 짓고 보장한 흐름 ──────────────────────────
@dataclass(frozen=True)
class StageDagGraph(Generic[C]):
    """실제로 돌 흐름. `order` 는 위상 순서이고 모든 간선이 앞으로만 간다.

    `given` 은 첫 단계가 돌기 전에 **이미 있는** 산출물이다 — 바깥에서 들어온 원본
    문서와, `--only` 로 앞칸을 뺐지만 디스크에 남아 있는 파일들이다.
    """
    name: str
    order: list[str]
    stages: dict[str, Stage[C]]
    edges: Edges
    given: list[Artifact[C]] = field(default_factory=lambda: [])

    @property
    def first(self) -> str | None:
        return self.order[0] if self.order else None

    def next_of(self, cur: str, kind: int) -> str | None:
        """이 갈래로 갈 다음 단계. 흐름이 끝나면 `None`."""
        d = self.edges.dest(cur, kind)
        if d is None or d == HALT:
            return None
        if d != NEXT:
            return d
        i = self.order.index(cur)
        return self.order[i + 1] if i + 1 < len(self.order) else None

    def render(self) -> str:
        """`--dry-run` 이 찍는 것. 폴백 간선까지 화면에 보인다."""
        lines = ["흐름 %s — 단계 %d" % (self.name, len(self.order))]
        for name in self.order:
            outs: list[str] = []
            for kind in KINDS:
                if not self.stages[name].emits & kind:
                    continue
                nxt = self.next_of(name, kind)
                if nxt is None:
                    # 순서상 다음이 없어 끝난 것과 HALT 로 멈춘 것을 갈라 적는다.
                    nxt = "(끝)" if self.edges.dest(name, kind) == NEXT else "(멈춤)"
                outs.append("%s→%s" % (KIND_NAME[kind], nxt))
            lines.append("  %-14s %s" % (name, " · ".join(outs)))
        return "\n".join(lines)


class GraphError(Exception):
    """팩토리가 지은 그래프가 검사를 통과하지 못했다. 단계는 하나도 돌지 않았다."""


def simulate(graph: StageDagGraph[C], ctx: C) -> list[str]:
    """아무것도 실행하지 않고 그래프만 걷는다. 불평 목록을 낸다(없으면 빈 목록).

    다섯을 본다 — 완결성 · 매달림 · 비순환 · 도달성 · 산출물 사슬.
    산출물 사슬은 **닿을 수 있는 모든 경로에서** 성립해야 한다. 가지가 생기면
    사람이 눈으로는 못 보는 자리라 이 검사가 손 검토보다 나은 유일한 이유다.
    """
    out: list[str] = []
    index = {n: i for i, n in enumerate(graph.order)}
    순환있음 = False

    # ① 완결성 · ② 매달림 · ③ 비순환
    for name in graph.order:
        stage = graph.stages[name]
        for kind in KINDS:
            if not stage.emits & kind:
                continue
            d = graph.edges.dest(name, kind)
            if d is None:
                out.append("완결성 — %s 의 %s 갈래에 간선이 없다" % (name, KIND_NAME[kind]))
                continue
            if d in (HALT, NEXT):
                continue
            if d not in graph.stages:
                out.append("매달림 — %s 의 %s 갈래가 없는 단계를 가리킨다: %s"
                           % (name, KIND_NAME[kind], d))
                continue
            if index[d] <= index[name]:
                out.append("순환 — %s 의 %s 갈래가 뒤로 간다: %s"
                           % (name, KIND_NAME[kind], d))
                순환있음 = True

    # ④ 도달성 — 첫 단계에서 어느 갈래로도 닿지 못하는 단계
    닿음: set[str] = set()
    if graph.first:
        더볼것 = [graph.first]
        while 더볼것:
            cur = 더볼것.pop()
            if cur in 닿음 or cur not in graph.stages:
                continue
            닿음.add(cur)
            for kind in KINDS:
                if not graph.stages[cur].emits & kind:
                    continue
                nxt = graph.next_of(cur, kind)
                if nxt:
                    더볼것.append(nxt)
    for name in graph.order:
        if name not in 닿음:
            out.append("도달성 — %s 로 가는 경로가 하나도 없다" % name)

    # ⑤ 산출물 사슬 — 순환이 있으면 앞 단계의 답이 아직 없어 셀 수 없다
    if 순환있음:
        return out
    # **갈래를 함께 담는다.** `OK` 로 나온 간선만 앞 단계의 `writes` 를 보장한다 —
    # `FAIL` 이나 `SKIP` 으로 떨어진 단계는 자기 산출물을 내지 않았다.
    앞선것: dict[str, list[tuple[str, int]]] = {n: [] for n in graph.order}
    for name in graph.order:
        for kind in KINDS:
            if not graph.stages[name].emits & kind:
                continue
            nxt = graph.next_of(name, kind)
            if nxt in 앞선것:
                앞선것[nxt].append((name, kind))
    보장됨: dict[str, set[str]] = {}
    처음부터 = {a.name for a in graph.given}
    for name in graph.order:
        ps = 앞선것[name]
        if ps:
            묶음: list[set[str]] = []
            for p, kind in ps:
                난것: set[str] = ({a.name for a in graph.stages[p].writes(ctx)}
                                 if kind == OK else set())
                묶음.append(보장됨[p] | 난것)
            교집합 = 묶음[0]
            for m in 묶음[1:]:
                교집합 = 교집합 & m
            보장됨[name] = 교집합
        else:
            보장됨[name] = set(처음부터)
        for art in graph.stages[name].reads(ctx):
            if art.name not in 보장됨[name]:
                out.append("산출물 — %s 가 읽는 %s 를 앞의 어떤 단계도 반드시 쓰지 않는다"
                           % (name, art.name))
    return out


def build_graph(name: str, order: Sequence[str], stages: Mapping[str, Stage[C]],
                edges: Edges, given: Sequence[Artifact[C]], ctx: C) -> StageDagGraph[C]:
    """흐름을 짓고 **그 자리에서 보장한다.** 어긋나면 단계를 하나도 돌리지 않고 죽는다.

    진입점에서 부른다 — 어떤 자식 프로세스도 띄우기 전에. 실패가 늦게 나면
    이미 파일을 쓴 뒤라 되돌리기 어렵다.
    """
    graph = StageDagGraph(name=name, order=list(order), stages=dict(stages),
                          edges=edges, given=list(given))
    complaints = simulate(graph, ctx)
    if complaints:
        raise GraphError("흐름 %s 가 어긋났다:\n  " % name + "\n  ".join(complaints))
    return graph


def existing(artifacts: Sequence[Artifact[C]], ctx: C) -> list[Artifact[C]]:
    """이미 디스크에 있는 산출물만 고른다. `build_graph` 의 `given` 에 넣는다.

    `--only build` 처럼 앞칸을 빼고 불러도 파일이 실제로 있으면 흐름이 성립한다.
    """
    return [a for a in artifacts if os.path.exists(a.locate(ctx))]


# ── 5. 드라이버 — 한 벌. 모드는 데이터(그래프)만 넘긴다 ──────────────────
class Pipeline(Generic[C]):
    """그래프를 따라 도는 루프. 세 실행기가 이 한 벌을 쓴다.

    `run` 은 **재정의할 수 있다.** 다만 재정의가 루프를 다시 쓰는 자리는 아니다 —
    `super().run()` 을 부르고 앞뒤에 자기 일을 붙이는 자리다.
    """

    def run(self, graph: StageDagGraph[C], ctx: C) -> list[StageRow]:
        rows: list[StageRow] = []
        cur = graph.first
        while cur:
            stage = graph.stages[cur]
            print("\n── %s ──────────────────────────────" % cur, flush=True)
            t0 = time.monotonic()
            missing = missing_reads(stage, ctx)
            if missing:
                why = "; ".join(missing)
                out = Outcome(FAIL, why, [{"stage": cur, "seconds": time.monotonic() - t0,
                                           "usage": M.normalize_usage(None),
                                           "ok": False, "why": why}])
            else:
                try:
                    # 쓸 산출물의 폴더는 드라이버가 보장한다. 단계와 자식 프로세스는 파일만 쓴다.
                    for art in stage.writes(ctx):
                        os.makedirs(os.path.dirname(art.locate(ctx)) or ".", exist_ok=True)
                    out = stage.perform(ctx)
                except msgspec.DecodeError as e:
                    # 단계 안에서 읽은 산출물의 꼴이 어긋났다. 여기가 예외를 받는 유일한 자리다.
                    why = "산출물 꼴이 어긋났다 — %s" % e
                    out = Outcome(FAIL, why, [{"stage": cur, "seconds": time.monotonic() - t0,
                                               "usage": M.normalize_usage(None),
                                               "ok": False, "why": why}])
                bad = bad_writes(stage, ctx) if out.kind == OK else []
                if bad:
                    why = "; ".join(bad)
                    for row in out.rows:
                        row["ok"], row["why"] = False, why
                    out = Outcome(FAIL, why, out.rows)
            rows.extend(out.rows)
            nxt = graph.next_of(cur, out.kind)
            if out.kind == FAIL and nxt is None:
                print("막힘 — 뒤 단계는 이 산출물에 기대므로 여기서 멈춘다.", file=sys.stderr)
            cur = nxt
        return rows


# ── 6. 구체 단계의 두 갈래 — 기계와 LLM ─────────────────────────────────
class MachineStage(Stage[C]):
    """자식 프로세스 하나. LLM 을 부르지 않으므로 토큰은 늘 0이고 행도 하나다.

    자식 프로세스를 띄우고 재는 코드는 이 `perform` 한 벌이다 — 갈리면 측정이 모드마다 달라진다.
    하위 클래스가 `perform` 을 재정의할 때는 `super().perform()` 을 감싸 앞뒤에 문맥만 붙이거나,
    부르기 전에 가로채 실패를 낸다. 가로챌 때는 측정 표의 행을 스스로 하나 낸다.
    """
    emits = OK | FAIL

    @abstractmethod
    def argv(self, ctx: C) -> list[str]:
        ...

    @abstractmethod
    def cwd(self, ctx: C) -> str:
        ...

    def perform(self, ctx: C) -> Outcome:
        t0 = time.monotonic()
        cwd = self.cwd(ctx)
        if not os.path.isdir(cwd):
            ok, why = False, "작업 디렉토리가 없다: %s" % cwd
        else:
            with M.Heartbeat(self.name, every=60.0):
                rc = subprocess.run(self.argv(ctx), cwd=cwd).returncode
            ok, why = (rc == 0), ("" if rc == 0 else "종료 코드 %d" % rc)
        seconds = time.monotonic() - t0
        print("%s — %s (%s)" % (self.name, "성공" if ok else "실패", M.hms(seconds)),
              flush=True)
        return Outcome(OK if ok else FAIL, why,
                       [{"stage": self.name, "seconds": seconds,
                         "usage": M.normalize_usage(None), "ok": ok, "why": why}])


# `claude -p` 한 세션의 결과. `(라벨, 걸린 초, 종료 코드, 결과 또는 None)`.
JobResult = tuple[str, float, int, AgentResult | None]


def run_agent_with(model: str, repo: str, root: str, prompt: str,
                   timeout: float | None = None,
                   label: str | None = None) -> tuple[float, int, AgentResult | None]:
    """`claude -p` 를 한 번 부른다. `(걸린 초, 종료 코드, 결과 또는 None)`.

    **배치별 시간을 여기서 잰다** — 부르는 쪽은 병렬이라 층 전체만 잴 수 있다.

    **하트비트를 여기 두지 않는다.** 동시에 도는 배치가 저마다 찍으면 화면을 못 읽는다 —
    층 하나를 감싸는 하트비트 하나를 `run_layer` 를 부르는 쪽이 건다.
    """
    argv = M.claude_argv(model=model, repo=repo, extra_dirs=[root])
    t0 = time.monotonic()
    p = subprocess.run(argv, input=prompt, cwd=repo,
                       capture_output=True, text=True, timeout=timeout)
    seconds = time.monotonic() - t0
    try:
        return seconds, p.returncode, M.parse_result(p.stdout)
    except msgspec.DecodeError as e:
        print("[%s] 결과 JSON 이 꼴에 안 맞는다 — %s" % (label or "?", e), file=sys.stderr)
        tail = (p.stderr or p.stdout or "")[-800:]
        if tail:
            print("[%s] %s" % (label or "?", tail), file=sys.stderr)
        return seconds, p.returncode, None


def run_layer(model: str, repo: str, root: str, jobs: Sequence[tuple[str, str]],
              concurrency: int = 8,
              timeout: float | None = None) -> list[JobResult]:
    """한 층 = 동시에 최대 `concurrency` 개. 층 사이는 부르는 쪽이 순차로 돈다.

    `jobs` 는 `[(라벨, 프롬프트), …]`. 낸 것은 `[(라벨, 초, 종료코드, 결과 또는 None), …]`
    이고 **라벨 순서로 정렬**해서 낸다 — 끝나는 순서는 실행마다 흔들린다.

    **한 배치가 터져도 층을 버리지 않는다.** 터진 배치는 종료 코드 -1 · 결과 None 인
    행으로 남고, 부르는 쪽이 실패로 센다.
    """
    if not jobs:
        return []
    rows: list[JobResult] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as ex:
        futs = {ex.submit(run_agent_with, model, repo, root, prompt, timeout, label): label
                for label, prompt in jobs}
        for f in futs:
            label = futs[f]
            try:
                rows.append((label,) + f.result())
            except Exception as ex_:                      # noqa: BLE001 — 층을 살린다
                print("[%s] 배치가 터졌다: %s" % (label, ex_), file=sys.stderr)
                rows.append((label, 0.0, -1, None))
    return sorted(rows, key=lambda r: r[0])


SECTION = re.compile(r"^<!-- section: ([a-z0-9-]+) -->\n", re.MULTILINE)
SECTION_LIKE = re.compile(r"^[ \t]*<!--\s*section\b.*$", re.MULTILINE | re.IGNORECASE)

class PromptEnvironment(jinja2.Environment):
    """프롬프트 글의 Jinja2 환경. 사전 값의 `.이름` 은 열쇠를 먼저 찾는다 — `items` · `values` 열쇠가 dict 메서드에 가리지 않는다."""

    def getattr(self, obj: object, attribute: str) -> object:
        if isinstance(obj, Mapping) and attribute in obj:
            return cast(Mapping[str, object], obj)[attribute]
        return super().getattr(obj, attribute)


def _printable(value: object) -> object:
    """`{{ }}` 로 찍히는 값. `None` 과 호출 가능한 것(메서드 · 함수)은 글이 될 수 없어 `TemplateError` 다."""
    if isinstance(value, jinja2.Undefined):
        return value
    if value is None or callable(value):
        raise TemplateError("찍을 수 없는 값 %r" % (value,))
    return value


# 블록 태그만 있는 줄은 빈 줄을 남기지 않는다(태그 뒤에 공백이 없을 때). 글 끝 줄바꿈은 그대로 둔다. 값은 이스케이프하지 않는다.
PROMPT_ENV = PromptEnvironment(undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                               keep_trailing_newline=True, autoescape=False, finalize=_printable)


class PromptResource:
    """프롬프트 글을 리소스 파일에서 읽는 단계의 믹스인. 단계당 파일 하나 `<prompt_dir>/<파일>.md`.

    파일 안은 `<!-- section: 이름 -->` 줄로 절을 가를 수 있다. 단계는 읽는 이름을 `prompt_names` 에
    `"<파일>"` 또는 `"<파일>#<절>"` 로 선언한다. 선언 밖은 읽지 않는다 — `test/test_prompt_resources.py` 가
    선언과 디스크의 파일 · 절을 1:1 로 대조한다.
    """
    prompt_dir: ClassVar[str] = ""
    prompt_names: ClassVar[tuple[str, ...]] = ()

    @staticmethod
    def sections(text: str) -> dict[str, str]:
        """절 이름 → 글. 표식이 없으면 `{"": 본문}`. 글은 앞뒤 줄바꿈을 떼고 줄바꿈 하나로 끝낸다.

        표식처럼 보이는 줄(`<!-- section` 으로 시작)이 `SECTION` 꼴이 아니면 `ValueError` 다.
        """
        bad = [m.group(0) for m in SECTION_LIKE.finditer(text) if not SECTION.match(text, m.start())]
        if bad:
            raise ValueError("절 표식 꼴이 틀렸다: %r" % bad[0])
        marks = list(SECTION.finditer(text))
        if not marks:
            return {"": text.strip("\n") + "\n"}
        if text[:marks[0].start()].strip():
            raise ValueError("첫 절 표식 앞에 글이 있다")
        out: dict[str, str] = {}
        for i, m in enumerate(marks):
            if m.group(1) in out:
                raise ValueError("절 %r 이 두 번 나온다" % m.group(1))
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            out[m.group(1)] = text[m.end():end].strip("\n") + "\n"
        return out

    @staticmethod
    def free_names(text: str) -> set[str]:
        """Jinja2 글 `text` 가 값으로 받아야 하는 이름들 — 타지 않는 `{% if %}` 갈래 안의 것도 센다.

        Jinja2 문법 오류와 환경에 없는 필터 · 검사(타지 않는 갈래 안의 것도)는 `TemplateError` 다.
        """
        try:
            ast = PROMPT_ENV.parse(text)
            free = jinja2.meta.find_undeclared_variables(ast)    # 컴파일을 거쳐 타는 갈래의 없는 필터도 여기서 난다
        except jinja2.TemplateSyntaxError as e:
            raise TemplateError("Jinja2 문법 — 글의 %d 줄: %s" % (e.lineno, e.message)) from e
        unknown = sorted({n.name for n in ast.find_all(jinja2.nodes.Filter) if n.name not in PROMPT_ENV.filters}
                         | {n.name for n in ast.find_all(jinja2.nodes.Test) if n.name not in PROMPT_ENV.tests})
        if unknown:
            raise TemplateError("Jinja2 문법 — 없는 필터 · 검사 %s" % unknown)
        return free

    @staticmethod
    def render_text(text: str, /, **values: object) -> str:
        """Jinja2 글 `text` 를 `values` 로 렌더한다(`PROMPT_ENV`).

        `free_names` 가 내는 이름과 넘긴 값의 이름이 같아야 한다. 그래서 `default` 는 이름이 없을 때 쓰이지 않는다 —
        빈 값 대체는 `{{ x or "대체" }}` 로 쓴다. 이 어긋남 · `free_names` 의 오류 · 렌더 중 오류(없는 속성 · 열쇠 ·
        `None` · 형이 안 맞는 연산)는 모두 `TemplateError` 다.
        """
        free = PromptResource.free_names(text)
        missing, unused = sorted(free - set(values)), sorted(set(values) - free)
        if missing or unused:
            raise TemplateError("값이 없는 자리 %s · 자리가 없는 값 %s" % (missing, unused))
        try:
            return PROMPT_ENV.from_string(text).render(values)
        except TemplateError:
            raise
        except jinja2.TemplateSyntaxError as e:
            raise TemplateError("Jinja2 문법 — 글의 %d 줄: %s" % (e.lineno, e.message)) from e
        except Exception as e:
            raise TemplateError("Jinja2 렌더 — %s: %s" % (type(e).__name__, e)) from e

    @classmethod
    def load_prompt(cls, name: str, /, **values: object) -> str:
        """`"<파일>"` 또는 `"<파일>#<절>"` 을 읽어 그 글을 `render_text` 로 렌더한다.

        선언 밖 이름 · 없는 절은 `KeyError`, 절대 경로가 아닌 `prompt_dir` · 틀린 절 표식은 `ValueError`,
        자리와 값의 어긋남 · Jinja2 오류는 `TemplateError` 다. 이름 인자가 위치 전용이라 자리 이름이 `name` 이어도 채워진다.
        """
        if name not in cls.prompt_names:
            raise KeyError("%s 는 프롬프트 %r 를 선언하지 않았다 (선언: %s)"
                           % (cls.__name__, name, ", ".join(cls.prompt_names) or "없음"))
        if not os.path.isabs(cls.prompt_dir):
            raise ValueError("%s.prompt_dir 은 절대 경로여야 한다: %r" % (cls.__name__, cls.prompt_dir))
        file, _, section = name.partition("#")
        with open(os.path.join(cls.prompt_dir, file + ".md"), encoding="utf-8") as f:
            parts = cls.sections(f.read())
        if section not in parts:
            raise KeyError("%s.md 에 절 %r 이 없다" % (file, section))
        return cls.render_text(parts[section], **values)


class LlmStage(PromptResource, Stage[C]):
    """LLM Model을 부르는 단계. 훅 여섯 중 `prompt` 와 `repo` 만 필수다.

    팬아웃은 단일 호출의 일반화다 — 세션 하나짜리 단계는 `jobs` 의 기본값이
    자기 이름 하나를 담은 목록을 내므로 훅을 하나도 더 구현하지 않는다.

    `perform` 을 재정의하지 않는다 — 층을 도는 방식과 측정이 갈리면 안 된다.
    """
    emits = OK | FAIL

    @abstractmethod
    def prompt(self, ctx: C) -> str:
        ...

    @abstractmethod
    def repo(self, ctx: C) -> str:
        """`claude -p` 가 열 저장소이자 자식 프로세스의 작업 폴더."""

    def model(self, ctx: C) -> str:
        return ctx.model

    def rounds(self, ctx: C) -> int:
        return 1

    def jobs(self, ctx: C, rnd: int) -> list[tuple[str, str]]:
        return [(self.name, self.prompt(ctx))]

    def harvest(self, ctx: C, got: Sequence[JobResult], rnd: int) -> Outcome:
        """세션마다 행 하나. 하나라도 실패하면 층이 실패다."""
        rows: list[StageRow] = []
        ok_all = True
        for label, seconds, rc, result in got:
            ok, why = M.agent_verdict(rc, result)
            ok_all = ok_all and ok
            rows.append({"stage": label, "seconds": seconds,
                         "usage": M.normalize_usage(result), "ok": ok, "why": why})
        return Outcome(OK if ok_all else FAIL,
                       "" if ok_all else "세션이 실패했다", rows)

    def perform(self, ctx: C) -> Outcome:
        rows: list[StageRow] = []
        for rnd in range(self.rounds(ctx)):
            jobs = self.jobs(ctx, rnd)
            with M.Heartbeat(self.name):
                got = run_layer(self.model(ctx), self.repo(ctx), ctx.root, jobs,
                                concurrency=ctx.concurrency, timeout=ctx.timeout)
            out = self.harvest(ctx, got, rnd)
            rows.extend(out.rows)
            if out.kind != OK:
                return Outcome(out.kind, out.why, rows)
        return Outcome(OK, "", rows)
