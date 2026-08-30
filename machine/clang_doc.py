#!/usr/bin/env python3
# <include file="machine/comments.xml" path="//term[@id='clang_doc.py']"/>
# clang-doc 가 여러 파일로 흩뿌린 결과를 심볼 목록 하나로 모으는 도구.
# 쓰는 것: load_clang_doc · 쓰이는 곳: 없음
"""clang_doc.py — clang-doc 이 흩뿌린 JSON 을 평평한 심볼 목록 하나로 모은다.

clang-uml 은 클래스 도구라 네임스페이스 안 자유 함수를 내지 않는다. clang-doc 이
그 함수 층을 `파일:줄`과 함께 채운다.

이 파일은 관계를 만들지 않는다. 합성/집약/의존의 구분은 `clang-uml` 에만 있고
`normalize.py` 가 그쪽에서 가져온다. 여기서 내는 것은 심볼과 그 좌표뿐이다.

형식의 급소 다섯 — 전부 틀려도 오류가 나지 않는 자리다:

  ① `Namespace` 가 안쪽부터 온다 — `["Panorama","Core","SJH"]`. 뒤집어야
     `SJH::Core::Panorama` 가 되고, 그래야 1차 판정의 네임스페이스 허용목록에 걸린다.
  ② `Location` 이 없는 요소가 섞인다 — 정의를 못 본 타입이다. 버린다.
  ③ `Description` 이 리스트의 리스트다. `TextComment` 글자만 순서대로 이어 붙인다.
  ④ `index.json` 의 `Records` 배열은 얕은 참조다 — 이름과 USR 뿐 Location 이 없다.
     실제 위치는 맹글링된 개별 파일에만 있어, index.json 만 훑으면 클래스가 0개가 된다.
     두 종류를 다 읽어야 한다.
  ⑤ 전역 네임스페이스를 `"GlobalNamespace"` 라는 가짜 이름으로 준다. 이름이 아니라 없음이다.

  python3 clang_doc.py <clang-doc 출력 디렉토리>      # 요약을 찍어 본다
"""
import json
import os
import sys
from typing import Any, TypedDict, cast

# clang-doc 이 전역 네임스페이스에 붙이는 가짜 이름. 이름이 아니라 "없음" 이다.
GLOBAL_NAMESPACE = "GlobalNamespace"

# TagType -> codegraph 의 kind. 목록에 없는 것은 class 로 본다.
# `terms_db.py` 의 KINDS 가 class·struct·enum·function 을 이미 받는다(확인함).
RECORD_KIND = {"class": "class", "struct": "struct", "union": "union"}


class Symbol(TypedDict):
    """이 파일이 내는 심볼 하나. `normalize.py::merge_clang_doc` 이 그대로 받아 읽는 꼴이다.

    이 TypedDict 가 없으면 타입 검사기가 `_symbol` 의 반환 dict 값 타입을 전 필드의
    합집합으로 뭉뚱그려 `kind` 까지 `None` 가능으로 읽는다.
    """
    name: str
    kind: str
    namespace: str
    file: str
    line: int
    signature: str
    doc: str


# <include file="machine/comments.xml" path="//term[@id='qualified_namespace']"/>
# 심볼이 속한 이름 공간을 바깥부터 이어 한 낱말로 만든다.
# 쓰는 것: 없음 · 쓰이는 곳: _symbol
def qualified_namespace(item: dict[str, Any]) -> str:
    """`Namespace` 배열을 바깥부터의 `A::B::C` 로 편다.

    급소 ① — clang-doc 은 안쪽부터 준다. 그대로 이으면 `Panorama::Core::SJH` 가 되어
    `CPP_FIRST_PARTY_NS` 허용목록이 통째로 빗나간다.
    급소 ⑤ — `GlobalNamespace` 는 이름이 아니라 없음이라 빼고 잇는다.
    """
    namespaces: list[Any] = item.get("Namespace") or []
    parts: list[str] = [p for p in reversed(namespaces) if p != GLOBAL_NAMESPACE]
    return "::".join(parts)


# <include file="machine/comments.xml" path="//term[@id='flatten_description']"/>
# 저자가 코드에 단 설명 글을 한 줄로 편다.
# 쓰는 것: 없음 · 쓰이는 곳: _symbol
def flatten_description(desc: Any) -> str:
    """저자 문서 주석에서 글자만 순서대로 뽑아 한 줄로 잇는다.

    급소 ③ — `Description` 은 `{"ParagraphComments": [[{"TextComment": "…"}, …]]}` 처럼
    리스트의 리스트다. 문단·인자·반환 주석이 서로 다른 키에 담기므로 키 이름을 열거하지 않고
    구조를 훑어 `TextComment` 만 모은다. 각 조각은 앞에 공백 하나를 달고 오므로 깎아서 잇는다.
    """
    out: list[str] = []

    def walk(node: Any) -> None:
        # cast 근거 — isinstance 는 원소 타입을 모르는 `dict[?, ?]` · `list[?]` 까지만
        # 좁혀 준다. JSON 이라 원소는 무엇이든 올 수 있고 walk 가 다시 받아 걸러 낸다.
        # 런타임 검사는 바로 위 isinstance 가 이미 했다.
        if isinstance(node, dict):
            for key, value in cast(dict[str, Any], node).items():
                if key == "TextComment" and isinstance(value, str):
                    out.append(value.strip())
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in cast(list[Any], node):
                walk(value)

    walk(desc)
    return " ".join(p for p in out if p).strip()


# <include file="machine/comments.xml" path="//term[@id='function_signature']"/>
# 함수가 무엇을 받고 무엇을 돌려주는지 한 줄로 적는다.
# 쓰는 것: 없음 · 쓰이는 곳: load_clang_doc
def function_signature(item: dict[str, Any]) -> str:
    """사람이 읽는 한 줄 시그니처. `bool ApplyHomography(const cv::Mat & image, …)`."""
    ret_type: dict[str, Any] = item.get("ReturnType") or {}
    ret: str = ret_type.get("Name") or ""
    args: list[str] = []
    params: list[Any] = item.get("Params") or []
    for param in params:
        param_type: dict[str, Any] = param.get("Type") or {}
        type_name: str = param_type.get("Name") or ""
        name: str = param.get("Name") or ""
        args.append(f"{type_name} {name}".strip())
    head = f"{ret} {item.get('Name') or ''}".strip()
    return f"{head}({', '.join(args)})"


# <include file="machine/comments.xml" path="//term[@id='_symbol']"/>
# 도구가 낸 항목 하나를 우리 공통 꼴로 옮긴다.
# 쓰는 것: qualified_namespace, flatten_description · 쓰이는 곳: load_clang_doc
def _symbol(item: dict[str, Any], kind: str, signature: str = "") -> Symbol | None:
    """공통 꼴로 옮긴다. 급소 ② — 위치가 없으면 None 을 돌려 버리게 한다."""
    loc: dict[str, Any] = item.get("Location") or {}
    file_name: str | None = loc.get("Filename")
    line: int | None = loc.get("LineNumber")
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


# <include file="machine/comments.xml" path="//term[@id='_json_root']"/>
# 결과가 실제로 놓인 폴더를 고른다.
# 쓰는 것: 없음 · 쓰이는 곳: load_clang_doc
def _json_root(out_dir: str) -> str:
    """`clang-doc --output <D>` 는 `<D>/json/` 을 만든다. 둘 중 어느 쪽을 받아도 되게 한다."""
    nested = os.path.join(out_dir, "json")
    return nested if os.path.isdir(nested) else out_dir


# <include file="machine/comments.xml" path="//term[@id='load_clang_doc']"/>
# 흩어진 결과를 모아 평평한 심볼 목록으로 만든다.
# 쓰는 것: _json_root, _symbol, function_signature · 쓰이는 곳: clang_doc.py
def load_clang_doc(out_dir: str) -> list[Symbol]:
    """clang-doc 의 흩어진 산출물을 모아 평평한 심볼 목록으로 만든다.

    돌려주는 꼴: `[{"name","kind","namespace","file","line","signature","doc"}]`
    `(file, line, name)` 으로 정렬해 몇 번을 읽어도 같은 순서를 낸다 — 파일 시스템의
    나열 순서에 기대면 기계마다 codegraph.json 의 노드 번호가 달라진다.

    두 종류를 다 읽는 이유가 급소 ④다. `index.json` 에는 `Functions` 와 `Enums` 가
    위치까지 통째로 들어 있지만 `Records` 는 이름뿐인 참조라 위치가 없다. 레코드의 실체는
    맹글링된 개별 파일에 있어 그쪽을 따로 훑는다. 파일 이름이 맹글링된 심볼이라
    경로로 찾지 않고 내용의 `InfoType` 으로 가른다.
    """
    root = _json_root(out_dir)
    if not os.path.isdir(root):
        return []

    by_key: dict[str | tuple[str, int, str], Symbol] = {}

    def add(item: dict[str, Any], kind: str, signature: str = "") -> None:
        sym = _symbol(item, kind, signature)
        if sym is None:
            return
        # 같은 심볼이 두 파일에 나올 수 있다(중첩 레코드). USR 이 있으면 그것이 신원이고,
        # 없으면 좌표와 이름으로 대신한다.
        key: str | tuple[str, int, str] = (
            item.get("USR") or (sym["file"], sym["line"], sym["name"]))
        by_key.setdefault(key, sym)

    for dir_path, _dirs, files in os.walk(root):
        for name in sorted(files):
            if not name.endswith(".json"):
                continue
            try:
                raw: Any = json.load(open(os.path.join(dir_path, name), encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(raw, dict):
                continue
            # cast 근거 — isinstance 는 `dict[?, ?]` 까지만 좁혀 주는데, clang-doc 이 내는
            # JSON 객체는 키가 전부 문자열이다. 런타임 검사는 위 isinstance 가 이미 했다.
            doc = cast(dict[str, Any], raw)
            if name == "index.json":
                functions: list[Any] = doc.get("Functions") or []
                for item in functions:
                    add(item, "function", function_signature(item))
                enums: list[Any] = doc.get("Enums") or []
                for item in enums:
                    add(item, "enum")
            elif doc.get("InfoType") == "record":
                # TagType 이 없으면 `or ""` 로 빈 문자열이 되고, 그것도 표에 없으니 class 다 —
                # 없을 때 class 로 보는 옛 동작 그대로다.
                add(doc, RECORD_KIND.get(doc.get("TagType") or "", "class"))

    return sorted(by_key.values(), key=lambda s: (s["file"], s["line"], s["name"]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법 — clang_doc.py <clang-doc 출력 디렉토리>", file=sys.stderr)
        sys.exit(1)
    symbols = load_clang_doc(sys.argv[1])
    counts: dict[str, int] = {}
    for s in symbols:
        counts[s["kind"]] = counts.get(s["kind"], 0) + 1
    print(f"심볼 {len(symbols)}개 — " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"저자 문서 주석이 붙은 심볼: {sum(1 for s in symbols if s['doc'])}")
