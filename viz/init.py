import os
import re
import sys
import subprocess

from typing import Any
DOC_DIRS: list[dict[str, Any]] = [
    {"dir": "specs", "re": re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)-design\.md$")},
    {"dir": "plans", "re": re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")}
]

from typing import Optional

def parseSpecFilename(basename: str, dir: str = "specs") -> Optional[dict[str, str]]:
    entry = next((d for d in DOC_DIRS if d["dir"] == dir), None)
    if not entry:
        return None
    m = entry["re"].match(basename)
    if not m:
        return None
    return {"date": m.group(1), "slug": m.group(2)}

def findSimilar(slug: str, candidates: list[str]) -> list[str]:
    similar = []
    for c in candidates:
        if c == slug:
            continue
        if slug in c or c in slug:
            similar.append(c)
        elif len(slug) >= 4 and len(c) >= 4 and slug[:4] == c[:4]:
            similar.append(c)
    return similar

def currentBuilderVersion(root: str) -> str:
    try:
        res = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], cwd=root, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "untagged"

def currentBranch(cwd: str) -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, capture_output=True, text=True)
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return ""

def reportDir(cwd: str, docDir: str, slug: str) -> str:
    return os.path.join(cwd, docDir, slug)

def hasReport(cwd: str, docDir: str, slug: str) -> bool:
    return os.path.exists(os.path.join(reportDir(cwd, docDir, slug), "data.ts"))

def listDocs(cwd: str) -> list[dict[str, str]]:
    docs = []
    for entry in DOC_DIRS:
        d = entry["dir"]
        abs_dir = os.path.join(cwd, d)
        if not os.path.exists(abs_dir):
            continue
        try:
            files = os.listdir(abs_dir)
            for file in files:
                parsed = parseSpecFilename(file, d)
                if parsed:
                    docs.append({"file": file, "dir": d, **parsed})
        except OSError:
            pass
    return docs

def writeSkeleton(dir: str, slug: str, date: str, specName: str, branch: str, version: str) -> None:
    os.makedirs(dir, exist_ok=True)
    
    data_ts = f"""import type {{ ReportData }} from "report-builder/types";

export const data: ReportData = {{
  builderVersion: {repr(version)},
  slug: {repr(slug)},
  specName: {repr(specName)},
  date: {repr(date)},
  branch: {repr(branch)},
  decisions: [],
  // 용어집 — Mode 1.5 가 낸 terms.json 을 여기에 옮겨 적는다.
  //   report-term collect <plan.md> <terms-db.json>  →  (스킬이 묻는다)  →  report-term grade  →  report-term emit
  // terms.json 의 {{ "용어": {{ TermMeans, UserMentalValue }} }} 를
  // {{ id, label, short, kind, mental }} 로 옮긴다. 자동 import 하지 않는다 — 이 파일은 사람이 읽는 파일이다.
  terms: [],
}};
"""
    with open(os.path.join(dir, "data.ts"), "w", encoding="utf-8") as f:
        f.write(data_ts)
        
    report_tsx = """import { Page, Section, DecisionTable, VerdictFooter } from "report-builder";
import { data } from "./data.js";

export { data };

export default function Report() {
  return (
    <Page data={data}>
      <Section title="결정 요약">
        <DecisionTable decisions={data.decisions} />
      </Section>
      <Section title="수용 판정 — 사용자 기입란">
        <VerdictFooter />
      </Section>
    </Page>
  );
}
"""
    with open(os.path.join(dir, "report.tsx"), "w", encoding="utf-8") as f:
        f.write(report_tsx)

def main() -> None:
    if len(sys.argv) < 2:
        sys.argv.append(None) # Make sure it has enough args
    slug = sys.argv[1]
    
    cwd = os.getcwd()
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    docs = listDocs(cwd)
    version = currentBuilderVersion(ROOT)
    
    if not slug:
        missing = [s for s in docs if not hasReport(cwd, s["dir"], s["slug"])]
        missing.sort(key=lambda x: x["date"], reverse=True)
        
        if not missing:
            print("모든 문서에 보고서가 있다.")
            sys.exit(0)
            
        width = max(len(s["slug"]) for s in missing) + 3 if missing else 0
        print("보고서가 없는 문서:")
        for s in missing:
            print(f"  {s['slug'].ljust(width)}{s['date']}  {s['dir']}/")
        print("\n사용법 — report-spec init <slug>")
        sys.exit(1)
        
    started = next((entry["dir"] for entry in DOC_DIRS if hasReport(cwd, entry["dir"], slug)), None)
    if started:
        data_file = os.path.join(reportDir(cwd, started, slug), "data.ts")
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r'builderVersion:\s*"([^"]+)"', content)
                old_version = m.group(1) if m else None
        except OSError:
            old_version = None
            
        print(f"{slug} — 기존 작업 파일이 있다. 이어서 쓴다(rev.2 방식).")
        print(f"  자리: {started}/{slug}")
        if old_version and old_version != version:
            print(f"경고 — builderVersion \"{old_version}\" 이 현재 \"{version}\" 과 다르다.")
            print(f"  옛 버전으로 빌드하려면: git worktree add /tmp/rb-{old_version} {old_version}")
        sys.exit(0)
        
    match = next((s for s in docs if s["slug"] == slug), None)
    
    if not match:
        print("에러 — 대응하는 원본 문서를 찾지 못했다:", file=sys.stderr)
        print(f"  specs/*-{slug}-design.md", file=sys.stderr)
        print(f"  plans/*-{slug}.md", file=sys.stderr)
        
        candidates = findSimilar(slug, [s["slug"] for s in docs])
        if candidates:
            width = max(len(c) for c in candidates) + 3
            print("\n비슷한 slug:", file=sys.stderr)
            for c in candidates:
                s = next(x for x in docs if x["slug"] == c)
                print(f"  {c.ljust(width)}{s['date']}  {s['dir']}/", file=sys.stderr)
        sys.exit(1)
        
    dir_path = reportDir(cwd, match["dir"], slug)
    try:
        with open(os.path.join(cwd, match["dir"], match["file"]), "r", encoding="utf-8") as f:
            content = f.read()
            titleMatch = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            specName = titleMatch.group(1).strip() if titleMatch else ""
    except OSError:
        specName = ""
        
    branch = currentBranch(cwd)
    
    writeSkeleton(dir_path, slug, match["date"], specName, branch, version)
    
    print(f"{slug} — 스켈레톤 생성: {dir_path}")
    print(f"  근거 문서: {match['dir']}/{match['file']}")

if __name__ == "__main__":
    main()
