#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='run_mode1.py']"/>
# Mode 1 파이프라인을 한 번에 돌리면서 단계마다 걸린 시간과 쓴 토큰을 재는 파일.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""Mode 1(코드베이스 위키) 파이프라인을 단계 기계 위에서 돌리고 단계마다 시간과 토큰을 재는 실행기.

## 열두 단계 — LLM 이 도는 칸은 **넷**이다

    lang-hint ─▶ lang-decide ─▶ detect-changes ─▶ collect-graph ─▶ schedule-batches ─▶ annotate-symbols
    ─▶ snapshot-sources ─▶ verify-terms ─▶ outline-wiki ─▶ write-wiki ─▶ publish-wiki ─▶ verify-wiki

전량(`--cold`)에는 `detect-changes` 가 없다 — 대조할 옛 지문이 없어서다. 단계 클래스와 전이표는
`runner/mode1/` 패키지에 있고, 이 파일은 `main` 과 옛 이름 재수출만 갖는다.

| 단계 | 기반 | 무엇 | 부르는 것 |
|---|---|---|---|
| `lang-hint` | LLM | 루트 문서를 읽혀 언어 하나를 제안받는다. 못 받아도 막지 않는다 | `claude -p` 1회(가장 싼 Model) |
| `lang-decide` | 기계 | 제안을 결정론으로 기각하거나 채택해 `lang-select.json` 을 쓴다 | `machine/lang_select.py` |
| `detect-changes` | 파이썬 | 옛 지문과 지금 소스를 대조해 `changes.json` 을 쓴다. 증분에만 | `machine/warmup.py` |
| `collect-graph` | 기계 | 정적 수집 → 코드 지도. 증분이면 diff 로 재수집 여부를 정한다 | `runner/wiki/prep.py` |
| `schedule-batches` | 파이썬 | 코드 지도를 의존 위상 층과 배치로 나눈다(`batches.json`) | `machine/survey_plan.py` |
| `annotate-symbols` | LLM | 전수조사. 계획과 diff 를 대조한 뒤 **층 오름차순 · 층 안 병렬**로 배치를 돌린다 | `claude -p` 배치마다 1회 |
| `snapshot-sources` | 파이썬 | 전수조사가 해낸 뒤에만 지문(`snapshot.json`)을 찍는다 | `machine/warmup.py` |
| `verify-terms` | 기계 | 읽기 레코드를 인용 검사(L1/L2/L3)하고 용어 DB 로 투영한다 | `machine/terms_db.py` |
| `outline-wiki` | LLM | 위키 목차 한 세션(`outline.json`). 이미 있으면 세션 없이 지나간다 | `claude -p` 1회 |
| `write-wiki` | LLM | 장마다 한 세션, 같은 층 순서 | `claude -p` 장마다 1회 |
| `publish-wiki` | 기계 | Mermaid 를 사전 렌더 SVG 로 바꾸고 VitePress 사이트를 짓는다 | `runner/wiki/build.py` |
| `verify-wiki` | 기계 | 산문의 인용을 저장소 실물과 대조한다 | `runner/wiki/check.py` |

**층 축은 "의존을 몇 개 갖는가"(out_deg)가 아니라 "얼마나 깊은가"(위상 깊이)다(K1).**
의존 하나만 가진 심볼도 그 하나가 3층이면 4층이다. 같은 층은 서로 의존하지 않으므로
병렬로 읽는다(K2 · K4). 배치는 8심볼(K3), 비노드 용어는 맨 마지막 층(K5), 위키도 같은
층 순서(K6), 고립 노드는 층0(K7)이다.

**지문 확정(`snapshot-sources`)은 `annotate-symbols` 바로 뒤다.** 관문이 감싸야 하는 것은
레코드를 만드는 단계다. 산문 뒤에 두면 산문 실패가 다음 실행의 전량 재조사를 부른다.

`verify-terms` 가 조사와 산문 사이에 있는 이유 — 산문을 쓰는 세션이 **인용 검사를 통과한**
`terms-db.json` 을 재료로 받게 하려는 것이다.

## 흐름은 진입점에서 미리 짓고 보장한다

`main` 이 인자를 읽자마자 `build_mode1_graph()` 를 부른다. 어떤 자식 프로세스도 띄우기 전이다 —
시뮬레이터가 완결성 · 매달림 · 비순환 · 도달성 · 산출물 사슬을 보고 어긋나면 `GraphError` 로 죽는다.
`--dry-run` 은 그 그래프를 `render()` 로 찍고, 코드 지도가 있으면 층 계획을 미리 보인다.

옛 단계 이름(`lang-select` · `prep` · `warmup` · `survey-plan` · `survey` · `warmup-save` · `terms` ·
`wiki` · `build` · `check`)은 `--only` · `--skip` 에서 그대로 쓸 수 있다 — `mode1.edges.ALIASES`.

## Model을 정하는 자리는 하나뿐이다

`config/mode1.toml` 의 `[models] sessions` 가 `mode1.context.load_config` 를 거쳐 `main` 의 `--model`
기본값이 되고, `Mode1Context.model` 로 들어가 `LlmStage.perform` -> `run_layer` -> `run_agent_with`
-> `claude_argv` 사슬을 그대로 타고 내려간다. **중간에서 Model을 바꾸지 않는다.** `lang-hint` 만
같은 파일의 `[models] lang_hint` 로 가장 싼 Model 을 따로 쓴다.

이 파일 자신은 Model이 아니다. 층 순서 · 배치 묶기 · 샤드 병합 · 키 충돌 해소를 전부
결정론으로 하고, Model을 부르는 자리는 자식 세션뿐이다. 그래서 **이 스크립트를 실행하는
세션의 Model은 여기서 강제되지 않고, `--json` 이 남기는 `model` 칸에도 들어가지 않는다** —
그 칸은 자식 세션의 값이다.

## 재는 자리 넷

  1. **벽시계 시간** — 단계마다 `time.monotonic()` 으로 감싼다. 파이썬이 재므로
     `claude` 가 무엇을 보고하든 상관없이 사람이 기다린 시간 그대로다.
  2. **토큰** — `claude -p --output-format json` 이 내는 `usage` 를 읽는다. 넷으로
     쪼개져 온다(입력 · 출력 · **캐시 읽기** · **캐시 생성**). **캐시 둘을 빼면 실제
     흘러간 양의 일부만 세게 된다.**
  3. **비용** — 같은 JSON 의 `total_cost_usd`.
  4. **턴 수** — `num_turns`. 에이전트가 몇 번 왕복했는지.

## 함정

- **`claude` 는 막혀도 종료 코드 0 을 낼 수 있다.** `is_error` 와 `subtype` 을 봐야 한다
  (`agent_verdict`).
- **`terms_db.py` 에 정적 `codegraph.json` 을 안 주면 투영이 그 파일을 덮어쓴다.**
  노드가 조용히 줄어든다(`VerifyTermsStage.terms_argv`).
- **경로를 박지 않는다.** 파이썬은 지금 도는 해석기(`sys.executable`), 나머지는 PATH 다.
  **예외 하나** — `_bootstrap_venv()` 는 `.venv` 밖 해석기로 불렸을 때 `.venv/bin/python3` 로
  재실행한다(파일 맨 위, `import survey_plan` 보다 먼저 — networkx 를 그 import 가 곧장 문다).
  경로 해석은 여기서 끝나고 그 아래 어떤 함수도 `.venv` 를 모른다.

## 쓰는 법

    .venv/bin/python runner/run_mode1.py <저장소> [--model <Model ID>]
                                            [--only prep,check] [--skip wiki]
                                            [--concurrency 8] [--target 8] [--hops 1]
                                            [--json 측정.json] [--dry-run]
                                            [--cold] [--resume]

**전량 조사는 `--cold`** 다 — 옛 지문으로 좁히지 않는다. 멈춘 실행은 `--resume` 으로 그 단계부터.
"""
import os
import sys


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1._bootstrap_venv']"/>
# 이 스크립트를 돌리는 파이썬이 .venv 안의 것인지 확인하고, 아니면 .venv 파이썬으로 바꿔서 다시 실행하는 함수다.
# 쓰는 것: os, sys · 쓰이는 곳: 없음
def _bootstrap_venv() -> None:
    """`.venv` 밖 해석기로 불렸으면 이 파일 안에서만 `.venv` 로 재실행한다.

    survey_plan.py 가 networkx 를 곧장 import 하므로, 그 import 가 일어나기 전에
    해석기 자체를 바꿔치기해야 한다. 재실행된 프로세스가 그대로 끝까지 돌고 끝나므로
    별도의 "해제" 코드는 없다 — 다른 코드는 여전히 `sys.executable` 만 본다.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_dir = os.path.join(repo_root, ".venv")
    venv_python = os.path.join(venv_dir, "Scripts", "python.exe") if sys.platform == "win32" \
        else os.path.join(venv_dir, "bin", "python3")
    if not os.path.exists(venv_python):
        return
    # sys.executable 을 realpath 로 비교하면 안 된다 — .venv/bin/python3 는 시스템 파이썬
    # 바이너리로 가는 심볼릭 링크라, realpath 를 풀면 venv 밖의 실제 경로와 같아져 버려서
    # "이미 venv 안" 으로 오판하고 재실행을 건너뛴다. sys.prefix 는 pyvenv.cfg 로 정해지므로
    # 심볼릭 링크를 풀지 않은 채로도 정확히 venv 인지 아닌지를 가른다.
    if os.path.abspath(sys.prefix) == os.path.abspath(venv_dir):
        return
    os.execv(venv_python, [venv_python] + sys.argv)


_bootstrap_venv()

import argparse
import json
import time
from collections.abc import Sequence
from typing import Literal, cast

# 러너는 `runner/`, 결정론 기계는 `machine/` 이다. 이 파일이 CLI 로 돌 때 sys.path[0] 은
# `runner/` 라 machine 을 못 찾는다 — 그래서 여기서 넣는다.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "machine"
    ),
)
import survey_plan  # noqa: E402

# 재는 코드의 원본은 `runner/measure.py` 하나다. 여기에 사본이 없다.
# 옛 이름으로 부르는 곳이 있어 그대로 다시 내보낸다.
import pipeline as P  # noqa: E402
from measure import (  # noqa: E402,F401
    AgentResult as AgentResult, Usage as Usage, StageRow as StageRow,
    Heartbeat as Heartbeat,
    normalize_usage as normalize_usage, sum_usage, agent_verdict as agent_verdict,
    claude_argv as claude_argv, hms, format_report, stage_totals,
)

# 형 · 자리 · 단계 바닥의 원본은 `mode1/` 패키지다. 옛 이름으로 부르는 시험이 있어 그대로 다시 내보낸다.
from mode1.context import (  # noqa: E402,F401
    Record as Record, Records as Records, WikiPage as WikiPage, reading_path as reading_path,
)
from mode1.machine_stage import Mode1Machine  # noqa: E402
from mode1.graph import ScheduleBatchesStage  # noqa: E402
from mode1.terms import VerifyTermsStage  # noqa: E402
wiki_argv = Mode1Machine.wiki_argv
plan_summary = ScheduleBatchesStage.plan_summary
terms_argv = VerifyTermsStage.terms_argv
from mode1.scan import SnapshotScan, DetectChangesStage  # noqa: E402
LANG_ALIAS = SnapshotScan.LANG_ALIAS
lang_of = SnapshotScan.lang_of
changed_seed = DetectChangesStage.changed_seed
from mode1.survey import AnnotateSymbolsStage  # noqa: E402
dep_excerpt = AnnotateSymbolsStage.dep_excerpt
survey_batch_prompt = AnnotateSymbolsStage.survey_batch_prompt
nonnode_prompt = AnnotateSymbolsStage.nonnode_prompt
merge_shards = AnnotateSymbolsStage.merge_shards
_qualified = AnnotateSymbolsStage.qualified
from mode1.wiki import OutlineWikiStage, WriteWikiStage  # noqa: E402
wiki_catalogue_prompt = OutlineWikiStage.wiki_catalogue_prompt
symbol_layers = WriteWikiStage.symbol_layers
page_layers = WriteWikiStage.page_layers
wiki_page_prompt = WriteWikiStage.wiki_page_prompt

# 팬아웃 호출의 원본은 `pipeline.py` 하나뿐이다. 여기에는 사본이 없다 —
# 시험 넷이 옛 이름을 참조하므로 이름 그대로 재수출한다.
run_agent_with = P.run_agent_with
run_layer = P.run_layer

# 이 파일은 <ROOT>/runner/ 에 있다. 저장소 뿌리는 그 위다 — 박지 않고 계산한다.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from mode1 import context as X  # noqa: E402
from mode1 import diff, resume  # noqa: E402
from mode1.context import Mode1Context  # noqa: E402
from mode1.edges import ORDER as STAGES, build_mode1_graph, graph_name  # noqa: E402
from mode1.edges import expand as expand, plan_stages as plan_stages  # noqa: E402


# <include file="machine/comments.xml" path="//term[@id='runner.run_mode1.main']"/>
# Mode 1(코드베이스 위키) 파이프라인 전체를 순서대로 돌리는 진입점 함수. 명령줄 인자를 읽고 어떤 단계를 돌릴지 정한 뒤 하나씩 실행하며 시간과 토큰을 잰다.
# 쓰는 것: runner.run_mode1.plan_stages, runner.run_mode1.run_warmup, runner.run_mode1.save_warmup, runner.run_mode1.run_lang_select, runner.run_mode1.run_survey (+8) · 쓰이는 곳: 없음
def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mode 1 파이프라인을 돌리고 단계별 시간·토큰을 잰다.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="대상 저장소 경로")
    ap.add_argument("--model", default=X.load_config()["models"]["sessions"], help="배치·장 세션이 쓸 Model")
    ap.add_argument("--concurrency", type=int, default=8, help="한 층에서 동시에 띄울 세션 수")
    ap.add_argument("--target", type=int, default=8, help="배치당 목표 심볼 수")
    ap.add_argument("--hops", type=int, default=1, help="바뀐 파일에서 파급을 몇 홉 퍼뜨릴지")
    ap.add_argument("--only", help="이 단계들만. 쉼표로 나눈다: " + ",".join(STAGES))
    ap.add_argument("--skip", help="이 단계들을 뺀다")
    ap.add_argument("--json", dest="json_out", help="측정값을 JSON 으로도 쓸 경로")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 돌릴지만 보이고 끝낸다")
    ap.add_argument("--timeout", type=float, default=None, help="에이전트 단계의 제한 시간(초)")
    ap.add_argument("--cold", action="store_true", help="전량. 옛 지문으로 좁히지 않는다")
    ap.add_argument("--resume", action="store_true", help="resume.json 이 있으면 멈춘 자리부터")
    ap.add_argument("--strategy", choices=("layer", "file"), default="layer",
                    help="annotate-symbols 전략. layer = 위상 층 · file = 파일 하나가 세션 하나, 가중치 순 (--cold 전용)")
    a = ap.parse_args(argv)

    repo = os.path.abspath(os.path.expanduser(cast(str, a.repo)))
    if not os.path.isdir(repo):
        print("에러 — 저장소가 없다: %s" % repo, file=sys.stderr)
        return 1
    model, only, skip = cast(str, a.model), cast(str | None, a.only), cast(str | None, a.skip)
    cold, dry_run, json_out = bool(a.cold), bool(a.dry_run), cast(str | None, a.json_out)
    strategy = cast(Literal["layer", "file"], a.strategy)
    if strategy == "file" and not cold:
        print("에러 — file 전략은 --cold 에서만 돈다. 파일 계획에는 증분 좁히기가 없다", file=sys.stderr)
        return 1
    ctx = Mode1Context(root=ROOT, model=model, timeout=cast(float | None, a.timeout),
                       concurrency=cast(int, a.concurrency), repo=repo,
                       target=cast(int, a.target), hops=cast(int, a.hops), cold=cold,
                       strategy=strategy)
    start = None
    if a.resume:
        start = resume.start_stage(resume.read_resume(X.RESUME.locate(ctx)), graph_name(ctx))
        if start is None:
            print("에러 — 이 그래프용 resume.json 이 없다", file=sys.stderr)
            return 1
    try:
        graph = build_mode1_graph(ctx, only=only.split(",") if only else None,
                                  skip=skip.split(",") if skip else None, start_at=start)
    except (ValueError, P.GraphError) as e:
        print("에러 — %s" % e, file=sys.stderr)
        return 1

    print("대상 %s" % repo)
    print("LLM Model %s · 흐름 %s · 단계 %s" % (model, graph.name, " -> ".join(graph.order)))
    if dry_run:
        print(graph.render())
        d = diff.read_diff(X.CHANGES.locate(ctx))
        cg = X.CODEGRAPH.locate(ctx)
        if "schedule-batches" in graph.order and os.path.exists(cg):
            narrowed = None if cold else (d["targets"] if d else None)
            cg_doc = cast(survey_plan.CodeGraph, P.load(cg, X.CodeGraphDoc))
            미리 = (survey_plan.plan_by_file(cg_doc) if ctx.strategy == "file"
                  else survey_plan.plan(cg_doc, ctx.target, only_files=narrowed))
            print("\n층 계획 (기계가 결정론으로 낸다)%s" % (" — diff 로 좁힘" if narrowed else ""))
            for line in ScheduleBatchesStage.plan_summary(미리):
                print(line)
        return 0

    t_all = time.monotonic()
    rows = P.Pipeline[Mode1Context]().run(graph, ctx)
    wall = time.monotonic() - t_all
    doc = resume.write_resume(X.RESUME.locate(ctx), graph.name, rows, graph.order)
    if doc:
        print("멈춤 — %s 에서. 재개: --resume  (%s)" % (doc["failed_at"], X.RESUME.locate(ctx)),
              file=sys.stderr)
    elif os.path.exists(X.RESUME.locate(ctx)):
        os.remove(X.RESUME.locate(ctx))

    print("\n" + "=" * 72)
    print("Mode 1 측정 — 전체 %s" % hms(wall))
    print("=" * 72)
    print(format_report(rows, wall_seconds=wall))
    print("\n단계 소계 — 병렬이라 행의 초 합계는 벽시계가 아니다")
    for name, u in stage_totals(rows).items():
        print("  %-16s 토큰 %12s · 턴 %3d · 비용 $%.4f"
              % (name, "{:,}".format(u["total"]), u["turns"], u["cost_usd"]))
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump({"repo": repo, "model": model, "graph": graph.name, "stages": rows,
                       "stage_totals": stage_totals(rows), "concurrency": ctx.concurrency,
                       "target": ctx.target, "total": sum_usage([r["usage"] for r in rows]),
                       "wall_seconds": wall}, f, ensure_ascii=False, indent=1)
        print("\n측정값 %s" % json_out)
    return 0 if all(r["ok"] or r.get("skipped") for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
