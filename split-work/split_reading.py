#!/usr/bin/env python3
"""terms-reading.json 을 두 저장소 몫으로 가른다 — `split_reading.py <원본> <mode1 출력> <mode2 출력>`.

판정은 `where` 의 경로 접두사다. 디렉토리는 `/` 로 끝나는 접두사, 파일은 글자 그대로.
FIRST(report-builder 몫인 machine/ 파일) → MODE1 → MODE2 → DROP 순으로 보고, 어디에도 없으면 공통 커널로
보아 둘 다 받는다. 반대편으로 건너가는 `uses[].to` 는 끊고 센다.
"""
import collections
import json
import sys

FIRST = ("machine/evidence.py", "machine/test_evidence.py", "machine/contract_types.py",
         "tools/gen_contract_types.py", "tools/test_gen_contract_types.py")
MODE1 = ("machine/", "runner/mode1/", "runner/wiki/", "runner/run_mode1.py", "runner/check_shard.py",
         "runner/test_mode1.py", "runner/test_run_mode1.py", "viz/render_classes.py",
         "viz/render_modules.py", "viz/demermaid.py", "viz/templates/dot/", "test/test_wiki.py",
         "bin/report-wiki", "config/mode1.toml", "tools/gen_contract.py", "tools/test_gen_contract.py",
         "evals/", "resources/")
MODE2 = ("runner/run_mode1_5.py", "runner/run_mode2.py", "runner/run_grade.py", "runner/term/",
         "runner/prompts/", "runner/test_run_mode1_5.py", "runner/test_run_mode2.py", "runner/test_run_grade.py",
         "viz/", "bin/report", "bin/report-spec", "bin/report-term", "tsconfig.json", "config/report.toml",
         "test/test_check.py", "test/test_components.py", "test/test_graph_math.py", "test/test_config.py",
         "test/test_init.py", "test/test_link_paths.py", "test/test_term.py",
         "test/test_wrap_terms.py", "test/svg.test.mjs", ".gemini/ReactRule.md")
DROP = ("runner/test_import_isolation.py",)


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
