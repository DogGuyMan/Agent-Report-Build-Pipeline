#!/usr/bin/env python3
"""terms-reading.json 을 두 저장소 몫으로 가른다 — `split_reading.py <원본> <mode1 출력> <mode2 출력>`.

판정은 `where` 의 경로 접두사다. 디렉토리는 `/` 로 끝나는 접두사, 파일은 글자 그대로.
FIRST(report-builder 몫인 src/codewiki/python/machine/ 파일) → MODE1 → MODE2 → DROP 순으로 보고, 어디에도 없으면 공통 커널로
보아 둘 다 받는다. 반대편으로 건너가는 `uses[].to` 는 끊고 센다.
"""
import collections
import json
import sys

FIRST = ("src/common/evidence.py", "test/common/test_evidence.py", "src/common/contract_types.py",
         "tools/gen_contract_types.py", "test/tools/test_gen_contract_types.py")
MODE1 = ("src/codewiki/python/machine/", "src/codewiki/python/runner/mode1/", "src/codewiki/python/runner/wiki/", "src/codewiki/python/runner/run_mode1.py", "src/codewiki/python/runner/check_shard.py",
         "test/codewiki/test_mode1.py", "test/codewiki/test_run_mode1.py", "src/codewiki/python/viz/render_classes.py",
         "src/codewiki/python/viz/render_modules.py", "src/codewiki/python/viz/demermaid.py", "resource/codewiki/templates/dot/", "qa/gates/test_wiki.py",
         "bin/report-wiki", "resource/codewiki/config.toml", "tools/gen_contract.py", "test/tools/test_gen_contract.py",
         "qa/evals/", "resource/codewiki/")
MODE2 = ("src/term/python/runner/run_mode1_5.py", "src/spec/python/runner/run_mode2.py", "src/term/python/runner/run_grade.py", "src/term/python/runner/term/",
         "runner/prompts/", "test/term/test_run_mode1_5.py", "test/spec/test_run_mode2.py", "test/term/test_run_grade.py",
         "viz/", "bin/report", "bin/report-spec", "bin/report-term", "tsconfig.json", "resource/spec/config.toml",
         "test/spec/test_check.py", "test/spec/test_components.py", "test/spec/test_graph_math.py", "test/spec/test_config.py",
         "test/spec/test_init.py", "test/spec/test_link_paths.py", "test/term/test_term.py",
         "test/spec/test_wrap_terms.py", "test/spec/svg.test.mjs", ".gemini/ReactRule.md")
DROP = ("test/core/test_import_isolation.py",)


def hit(path: str, rules: tuple[str, ...]) -> bool:
    return any(path == r or (r.endswith("/") and path.startswith(r)) for r in rules)


def side(where: str) -> set[str]:
    path = where.split(":")[0]
    if hit(path, FIRST):
        return {"mode2"}
    if hit(path, MODE1):
        return {"mode1"}
    if hit(path, MODE2):
        return {"mode2"}
    if hit(path, DROP):
        return set()
    return {"mode1", "mode2"}


def main(src: str, out1: str, out2: str) -> int:
    with open(src, encoding="utf-8") as f:
        db = json.load(f)
    sides = {k: side(r["where"]) for k, r in db.items()}
    out: dict[str, dict[str, object]] = {"mode1": {}, "mode2": {}}
    cut: collections.Counter[str] = collections.Counter()
    for key, rec in db.items():
        for s in sides[key]:
            copy = dict(rec)
            kept = [u for u in rec.get("uses", []) if u["to"] in db and s in sides[u["to"]]]
            cut[s] += len(rec.get("uses", [])) - len(kept)
            copy["uses"] = kept
            out[s][key] = copy
    for s, path in (("mode1", out1), ("mode2", out2)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out[s], f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"{s}: 레코드 {len(out[s])} · 끊은 uses {cut[s]} → {path}")
    print(f"둘 다 받은 레코드 {sum(1 for v in sides.values() if len(v) == 2)} · "
          f"버린 레코드 {sum(1 for v in sides.values() if not v)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
