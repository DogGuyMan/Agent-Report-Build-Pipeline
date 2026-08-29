#!/usr/bin/env python3
# <include file="docs/codegraph/comments.xml" path="//term[@id='clang_doc.py']"/>
# clang-doc 가 여러 파일로 흩뿌린 결과를 심볼 목록 하나로 모으는 도구.
# 쓰는 것: load_clang_doc · 쓰이는 곳: 없음
"""clang_doc.py — clang-doc 이 흩뿌린 JSON 을 평평한 심볼 목록 하나로 모은다.

**왜 필요한가.** C++ 쪽 수집기는 `clang-uml` 뿐인데 그것은 **클래스 도구**다.
🔵 2026-08-29 QtVisionEdit 실측 — clang-uml 이 낸 1차 노드 30개가 전부 타입이고
자유 함수는 **0개**였다. 그런데 이 저장소의 핵심 로직(`ComputePanorama` ·
`GetGoodMatches` · `BroadcastChannels`)은 네임스페이스 안 자유 함수라 함수 층이
통째로 비어 있었다. `clang-doc` 은 그 층을 채운다 — 실측 자유 함수 236개가
전부 `파일:줄`을 달고 나온다.

**이 파일은 관계를 만들지 않는다.** 합성/집약/의존의 구분은 `clang-uml` 에만 있고
`normalize.py` 가 그쪽에서 가져온다. 여기서 내는 것은 **심볼과 그 좌표**뿐이다.

**형식의 급소 다섯** (전부 틀려도 오류가 나지 않는 자리다):

  ① `Namespace` 가 **안쪽부터** 온다 — `["Panorama","Core","SJH"]`. 뒤집어야
     `SJH::Core::Panorama` 가 되고, 그래야 1차 판정의 네임스페이스 허용목록에 걸린다.
  ② `Location` 이 없는 요소가 섞인다 — Qt 의 QWidget 처럼 정의를 못 본 타입이다. 버린다.
  ③ `Description` 이 리스트의 리스트다. `TextComment` 글자만 순서대로 이어 붙인다.
  ④ **`index.json` 의 `Records` 배열은 얕은 참조다** — 이름과 USR 뿐 Location 이 없다.
     🔵 실측 — index.json 이 참조하는 record 64개가 **전량 Location 없음**이었다.
     실제 위치는 맹글링된 개별 파일(`_ZTVN3SJH6Server12SessionStoreE.json`)에만 있다.
     그래서 index.json 만 훑으면 클래스가 0개가 된다. **두 종류를 다 읽어야 한다.**
  ⑤ 전역 네임스페이스를 `"GlobalNamespace"` 라는 가짜 이름으로 준다. 이름이 아니라 없음이다.

거울 함정 경계 — 이 파일은 JSON 을 목록으로 펴는 스크립트다. 수집기는 둘 고정이므로
플러그인 구조·포맷 레지스트리·추상 인터페이스가 나오면 그 자체가 이 작업이 잡으려는 실패다.

  python3 clang_doc.py <clang-doc 출력 디렉토리>      # 요약을 찍어 본다
"""
import json
import os
import sys

# clang-doc 이 전역 네임스페이스에 붙이는 가짜 이름. 이름이 아니라 "없음" 이다.
GLOBAL_NAMESPACE = "GlobalNamespace"

# TagType -> codegraph 의 kind. 목록에 없는 것은 class 로 본다.
# `terms_db.py` 의 KINDS 가 class·struct·enum·function 을 이미 받는다(확인함).
RECORD_KIND = {"class": "class", "struct": "struct", "union": "union"}


# <include file="docs/codegraph/comments.xml" path="//term[@id='qualified_namespace']"/>
# 심볼이 속한 이름 공간을 바깥부터 이어 한 낱말로 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: _symbol
def qualified_namespace(item):
    """`Namespace` 배열을 바깥부터의 `A::B::C` 로 편다.

    급소 ① — clang-doc 은 **안쪽부터** 준다. `["Panorama","Core","SJH"]` 를 그대로 이으면
    `Panorama::Core::SJH` 가 되어 `CPP_FIRST_PARTY_NS` 허용목록이 통째로 빗나간다.
    급소 ⑤ — `GlobalNamespace` 는 이름이 아니라 없음이라 빼고 잇는다.
    """
    parts = [p for p in reversed(item.get("Namespace") or []) if p != GLOBAL_NAMESPACE]
    return "::".join(parts)


# <include file="docs/codegraph/comments.xml" path="//term[@id='flatten_description']"/>
# 저자가 코드에 단 설명 글을 한 줄로 편다.
# 쓰는 것: 없음 · 쓰이는 곳: _symbol
def flatten_description(desc):
    """저자 문서 주석에서 글자만 순서대로 뽑아 한 줄로 잇는다.

    급소 ③ — `Description` 은 `{"ParagraphComments": [[{"TextComment": "…"}, …]]}` 처럼
    리스트의 리스트다. 문단·인자·반환 주석이 서로 다른 키에 담기므로 키 이름을 열거하지 않고
    **구조를 훑어 `TextComment` 만 모은다.** 각 조각은 앞에 공백 하나를 달고 오므로 깎아서 잇는다.
    """
    out = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "TextComment" and isinstance(value, str):
                    out.append(value.strip())
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(desc)
    return " ".join(p for p in out if p).strip()


# <include file="docs/codegraph/comments.xml" path="//term[@id='function_signature']"/>
# 함수가 무엇을 받고 무엇을 돌려주는지 한 줄로 적는다.
# 쓰는 것: 없음 · 쓰이는 곳: load_clang_doc
def function_signature(item):
    """사람이 읽는 한 줄 시그니처. `bool ApplyHomography(const cv::Mat & image, …)`.

    clang-uml 에는 아예 없는 정보다. 전수조사 레코드의 `means` 를 쓸 때 인자 이름이
    있어야 무엇을 받는 함수인지 읽힌다.
    """
    ret = (item.get("ReturnType") or {}).get("Name") or ""
    args = []
    for param in item.get("Params") or []:
        type_name = (param.get("Type") or {}).get("Name") or ""
        name = param.get("Name") or ""
        args.append(f"{type_name} {name}".strip())
    head = f"{ret} {item.get('Name') or ''}".strip()
    return f"{head}({', '.join(args)})"


# <include file="docs/codegraph/comments.xml" path="//term[@id='_symbol']"/>
# 도구가 낸 항목 하나를 우리 공통 꼴로 옮긴다.
# 쓰는 것: qualified_namespace, flatten_description · 쓰이는 곳: load_clang_doc
def _symbol(item, kind, signature=""):
    """공통 꼴로 옮긴다. 급소 ② — 위치가 없으면 None 을 돌려 버리게 한다.

    위치 없는 심볼을 살려 두면 전수조사 레코드의 `where` 가 비어 인용 검증이 통째로 막힌다.
    """
    loc = item.get("Location") or {}
    file_name, line = loc.get("Filename"), loc.get("LineNumber")
    if not (file_name and line):
        return None
    return {
        "name": item.get("Name") or "",
        "kind": kind,
        "namespace": qualified_namespace(item),
        "file": file_name,
        "line": line,
        "signature": signature,
        "doc": flatten_description(item.get("Description")),
    }


# <include file="docs/codegraph/comments.xml" path="//term[@id='_json_root']"/>
# 결과가 실제로 놓인 폴더를 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: load_clang_doc
def _json_root(out_dir):
    """`clang-doc --output <D>` 는 `<D>/json/` 을 만든다. 둘 중 어느 쪽을 받아도 되게 한다."""
    nested = os.path.join(out_dir, "json")
    return nested if os.path.isdir(nested) else out_dir


# <include file="docs/codegraph/comments.xml" path="//term[@id='load_clang_doc']"/>
# 흩어진 결과를 모아 평평한 심볼 목록으로 만든다.
# 쓰는 것: _json_root, _symbol, function_signature · 쓰이는 곳: clang_doc.py
def load_clang_doc(out_dir):
    """clang-doc 의 흩어진 산출물을 모아 평평한 심볼 목록으로 만든다.

    돌려주는 꼴: `[{"name","kind","namespace","file","line","signature","doc"}]`
    `(file, line, name)` 으로 정렬해 **몇 번을 읽어도 같은 순서**를 낸다 — 파일 시스템의
    나열 순서에 기대면 기계마다 codegraph.json 의 노드 번호가 달라진다.

    두 종류를 다 읽는 이유가 급소 ④다. `index.json` 에는 `Functions` 와 `Enums` 가
    **위치까지 통째로** 들어 있지만 `Records` 는 이름뿐인 참조라 위치가 없다.
    레코드의 실체는 맹글링된 개별 파일에 있어 그쪽을 따로 훑는다. 파일 이름이 맹글링된
    심볼이라 **경로로 찾지 않고 내용의 `InfoType` 으로 가른다.**
    """
    root = _json_root(out_dir)
    if not os.path.isdir(root):
        return []

    by_key = {}

    def add(item, kind, signature=""):
        sym = _symbol(item, kind, signature)
        if sym is None:
            return
        # 같은 심볼이 두 파일에 나올 수 있다(중첩 레코드). USR 이 있으면 그것이 신원이고,
        # 없으면 좌표와 이름으로 대신한다.
        key = item.get("USR") or (sym["file"], sym["line"], sym["name"])
        by_key.setdefault(key, sym)

    for dir_path, _dirs, files in os.walk(root):
        for name in sorted(files):
            if not name.endswith(".json"):
                continue
            try:
                doc = json.load(open(os.path.join(dir_path, name), encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(doc, dict):
                continue
            if name == "index.json":
                for item in doc.get("Functions") or []:
                    add(item, "function", function_signature(item))
                for item in doc.get("Enums") or []:
                    add(item, "enum")
            elif doc.get("InfoType") == "record":
                add(doc, RECORD_KIND.get(doc.get("TagType"), "class"))

    return sorted(by_key.values(), key=lambda s: (s["file"], s["line"], s["name"]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법 — clang_doc.py <clang-doc 출력 디렉토리>", file=sys.stderr)
        sys.exit(1)
    symbols = load_clang_doc(sys.argv[1])
    counts = {}
    for s in symbols:
        counts[s["kind"]] = counts.get(s["kind"], 0) + 1
    print(f"심볼 {len(symbols)}개 — " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"저자 문서 주석이 붙은 심볼: {sum(1 for s in symbols if s['doc'])}")
