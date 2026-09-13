"""`detect-changes` · `snapshot-sources`. 옛 지문과 지금 소스를 대조하고, 조사가 해낸 뒤 지문을 찍는다."""
import os
import sys
import time

import declmap
import msgspec
import pipeline as P
import warmup
from mode1 import context as X
from mode1 import diff as D
from mode1.context import Mode1Context
from mode1.measured import Measured


class SnapshotScan:
    """옛 지문과 지금 소스를 대조하는 한 벌. `detect-changes` 와 `snapshot-sources` 가 상속한다.

    훑는 코드가 한 벌인 이유 — 전량 그래프에는 `detect-changes` 가 없어 `snapshot-sources` 가
    스스로 훑어야 하고, 두 단계가 다른 방식으로 훑으면 다음 실행의 증분 판정이 어긋난다.
    """
    # 코드 지도가 적는 언어 이름과 declmap 이 아는 이름이 한 칸 다르다. 수집기 판별을 여기서
    # 다시 하지 않는다 — 판별 규칙이 두 곳에 생기면 조용히 어긋난다.
    LANG_ALIAS = {"csharp": "cs", "python": "py"}

    @staticmethod
    def lang_of(codegraph_path: str | None) -> str | None:
        """코드 지도가 적어 둔 언어를 declmap 이 아는 이름으로 바꾼다.

        모르면 `None` 이다 — 예외가 아니다. 부르는 쪽이 증분 판정만 건너뛰고 나머지는 그대로 돈다.
        """
        if not codegraph_path:
            return None
        try:
            raw = P.load(codegraph_path, dict[str, object]).get("language")
        except (OSError, msgspec.DecodeError):
            return None
        if not isinstance(raw, str):
            return None
        name = SnapshotScan.LANG_ALIAS.get(raw, raw)
        return name if name in declmap.LANGS else None

    @staticmethod
    def lang_for(ctx: Mode1Context) -> str | None:
        """언어. `lang-select.json` 을 먼저, 없으면 코드 지도를 본다."""
        p = X.LANG_SELECT.locate(ctx)
        word = P.load(p, X.LangSelect)["language"] if os.path.exists(p) else None
        if word:
            name = SnapshotScan.LANG_ALIAS.get(word, word)
            return name if name in declmap.LANGS else None
        cg = X.CODEGRAPH.locate(ctx)
        return SnapshotScan.lang_of(cg if os.path.exists(cg) else None)

    @staticmethod
    def scan_snapshot(ctx: Mode1Context) -> tuple[warmup.Verdicts, warmup.Manifest, str] | None:
        """지금 소스를 훑어 옛 지문과 대조한다. `(판정, 새 지문, 지문 파일 경로)`.

        언어를 모르거나 git 이 아는 소스가 0개면 `None` — 전량으로 돈다.
        읽는 지문은 옛 이름(`warmup.json`)도 되고, 쓰는 경로는 늘 새 이름이다.
        """
        lang = SnapshotScan.lang_for(ctx)
        if lang is None:
            return None
        files = declmap.tracked_files(ctx.repo, lang, [])
        if not files:
            print("알림 — git 이 아는 %s 소스가 0개다. 전량 조사로 돈다." % lang, file=sys.stderr)
            return None
        decls, _ = declmap.scan(ctx.repo, lang, [], 0)
        판정, entries = warmup.status(X.snapshot_path(ctx), ctx.repo, files, decls)
        return 판정, entries, X.SNAPSHOT.locate(ctx)


class DetectChangesStage(SnapshotScan, Measured, P.Stage[Mode1Context]):
    """옛 지문과 지금 소스를 대조해 `changes.json` 을 쓴다. **증분 그래프에만 있다.**"""
    name = "detect-changes"

    def reads(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.LANG_SELECT]

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.CHANGES]

    @staticmethod
    def changed_seed(판정: warmup.Verdicts) -> list[str]:
        """다시 읽어야 할 파일의 씨앗. **`재읽기` 와 `위치만` 의 합집합이다.**

        `위치만` 을 반드시 포함한다 — `warmup.decl_hash` 는 선언의 이름만 해싱하므로 본문만
        바뀐 변경도 `위치만` 으로 판정된다. 레코드의 `does` 와 위키 산문의 행동 서술은 본문에
        달려 있어서, 이 갈래를 빼면 그 서술이 조용히 낡는다. `warmup.py` 의 CLI 도 같은 합집합을 쓴다.

        `유효` 는 읽을 것이 없고, `삭제됨` 은 읽을 파일 자체가 없다.
        """
        return sorted(set(판정.get("재읽기") or []) | set(판정.get("위치만") or []))

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        diff_path = X.CHANGES.locate(ctx)
        scanned = self.scan_snapshot(ctx)
        if scanned is None:
            empty: warmup.Verdicts = {"유효": [], "재읽기": [], "위치만": [], "삭제됨": []}
            print("알림 — 언어를 몰라 증분 판정을 건너뛴다. 전량 조사로 돈다.", file=sys.stderr)
            D.write_diff(diff_path, empty, None, ctx.hops, 0)
            ctx.targets = None
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        판정, entries, cache = scanned
        files_n = sum(len(v) for k, v in 판정.items() if k != "삭제됨")
        seed = self.changed_seed(판정)
        cg = X.CODEGRAPH.locate(ctx)
        # 파급까지 넓힌다. 코드 지도가 없으면 씨앗 그대로다 — 파급은 안전망이지 필수가 아니다.
        targets = warmup.blast_radius(cg, seed, ctx.hops) if seed and os.path.exists(cg) else seed
        D.write_diff(diff_path, 판정, targets, ctx.hops, files_n)
        ctx.targets, ctx.entries, ctx.warmup_cache, ctx.tracked_n = targets, entries, cache, files_n
        print("파일 %d개 — 유효 %d · 재읽기 %d · 위치만 %d · 삭제됨 %d"
              % (files_n, len(판정["유효"]), len(판정["재읽기"]), len(판정["위치만"]), len(판정["삭제됨"])))
        print("에이전트가 읽을 것 %d개 — 씨앗 %d개에서 %d홉 퍼뜨린 결과" % (len(targets), len(seed), ctx.hops))
        for p in targets[:15]:
            print("  " + p)
        if len(targets) > 15:
            print("  … 그 밖 %d개" % (len(targets) - 15))
        if 판정["삭제됨"]:
            print("사람이 볼 것 — 삭제된 파일 %d개의 레코드를 지울지 정해야 한다:" % len(판정["삭제됨"]),
                  file=sys.stderr)
            for p in 판정["삭제됨"][:10]:
                print("  " + p, file=sys.stderr)
        return P.Outcome(P.OK, "", [self.row(t0, True)])


class SnapshotSourcesStage(SnapshotScan, Measured, P.Stage[Mode1Context]):
    """전수조사가 해낸 뒤에만 지문을 찍는다.

    증분이면 `detect-changes` 가 넘긴 `entries` 를 찍고, 전량이면 **여기서 직접 훑어** 찍는다 —
    전량 그래프에는 `detect-changes` 가 없기 때문이다. 다음 실행이 이것을 옛 판으로 쓴다.
    """
    name = "snapshot-sources"

    def writes(self, ctx: Mode1Context) -> list[P.Artifact[Mode1Context]]:
        return [X.SNAPSHOT]

    def perform(self, ctx: Mode1Context) -> P.Outcome:
        t0 = time.monotonic()
        if ctx.entries is None:
            scanned = self.scan_snapshot(ctx)
            if scanned is None:
                print("알림 — 언어를 몰라 지문을 찍지 않는다.", file=sys.stderr)
                return P.Outcome(P.OK, "", [self.row(t0, True)])
            _, ctx.entries, ctx.warmup_cache = scanned
        if not ctx.warmup_cache:
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        if not ctx.survey_ok:
            print("지문을 갱신하지 않는다 — 전수조사가 실패했다. "
                  "지금 갱신하면 읽지 않은 파일이 '유효' 로 남는다.", file=sys.stderr)
            return P.Outcome(P.OK, "", [self.row(t0, True)])
        warmup.save(ctx.warmup_cache, ctx.entries)
        print("지문 갱신 — %s (%d개 파일)" % (ctx.warmup_cache, len(ctx.entries)))
        return P.Outcome(P.OK, "", [self.row(t0, True)])
