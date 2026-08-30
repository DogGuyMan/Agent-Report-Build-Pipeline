# <include file="machine/comments.xml" path="//term[@id='test_clang_doc.py']"/>
# clang-doc 적재기의 회귀 시험.
# 쓰는 것: 없음 · 쓰이는 곳: 없음
"""test_clang_doc.py — clang-doc 적재기의 회귀 시험."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clang_doc as CD  # noqa: E402
from clang_doc import Symbol  # noqa: E402

# ⚠ 이름 함정 — `test_normalize.py` 의 `CPP_REPO` 상수는 환경변수 `$GRAPHICS_REPO` 를 읽는다.
#   여기서 쓰는 `$CPP_REPO` 는 다른 저장소를 가리키므로 이름을 달리 적는다.
WIKI_CPP_REPO = os.path.expandvars(os.environ.get("CPP_REPO", "")) or "/골든저장소_미지정/CPP_REPO"


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc._write']"/>
# 테스트에서 쓸 가짜 clang-doc JSON 파일을 임시 디렉토리에 만들어주는 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_clang_doc.test_accepts_the_parent_directory_of_json, machine.test_clang_doc.test_description_absent_gives_empty_doc, machine.test_clang_doc.test_description_nested_text_is_flattened, machine.test_clang_doc.test_duplicate_usr_is_collapsed_and_order_is_deterministic, machine.test_clang_doc.test_enum_kind_and_location_come_from_index (+6)
def _write(root: str, rel: str, obj: object) -> str:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return path


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc._by_name']"/>
# clang_doc.load_clang_doc 이 돌려준 심볼 목록에서 이름이 name 과 같은 심볼을 정확히 하나 찾아주는 테스트 도우미 함수다.
# 쓰는 것: 없음 · 쓰이는 곳: machine.test_clang_doc.test_description_absent_gives_empty_doc, machine.test_clang_doc.test_description_nested_text_is_flattened, machine.test_clang_doc.test_enum_kind_and_location_come_from_index, machine.test_clang_doc.test_function_signature_has_return_type_and_params, machine.test_clang_doc.test_global_namespace_becomes_empty (+5)
def _by_name(syms: list[Symbol], name: str) -> Symbol:
    hits = [s for s in syms if s["name"] == name]
    assert len(hits) == 1, f"{name} 이 {len(hits)}개다"
    return hits[0]


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_namespace_is_reversed']"/>
# clang-doc가 네임스페이스를 안쪽에서 바깥쪽 순서로 주는데, 이걸 제대로 뒤집어서 합치는지 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 1. Namespace 는 안쪽부터 온다. 뒤집어 이어야 한다.
def test_namespace_is_reversed(tmp_path: Path):
    """네임스페이스를 뒤집어 이어 완전 수식 이름을 만든다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "ComputePanorama",
            "Namespace": ["Panorama", "Core", "SJH"],
            "Location": {"Filename": "core/panorama/panorama.cpp", "LineNumber": 129},
            "ReturnType": {"Name": "bool"}, "Params": [],
        }],
    })
    sym = _by_name(CD.load_clang_doc(root), "ComputePanorama")
    assert sym["namespace"] == "SJH::Core::Panorama"
    # 뒤집지 않은 꼴이 아님을 못박는다 — 이 자리가 조용히 틀리는 곳이다
    assert sym["namespace"] != "Panorama::Core::SJH"


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_global_namespace_becomes_empty']"/>
# clang-doc이 전역 네임스페이스를 "GlobalNamespace"라는 가짜 이름으로 표시하는데, 이게 실제로는 빈 문자열로 바뀌어야 함을 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 2. GlobalNamespace 는 이름이 아니라 "없음" 이다.
def test_global_namespace_becomes_empty(tmp_path: Path):
    """전역 네임스페이스라는 가짜 이름은 빈 문자열이 된다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "main", "Namespace": ["GlobalNamespace"],
            "Location": {"Filename": "app/gui.cpp", "LineNumber": 39},
            "ReturnType": {"Name": "int"}, "Params": [],
        }],
    })
    assert _by_name(CD.load_clang_doc(root), "main")["namespace"] == ""


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_symbol_without_location_is_dropped']"/>
# 위치 정보(파일명과 줄 번호)가 없는 심볼은 나중에 "어디"를 적을 수 없으니 아예 결과에서 빠져야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 3. Location 이 없는 요소는 버린다 — 위치 없는 노드는 `where` 를 못 만든다.
def test_symbol_without_location_is_dropped(tmp_path: Path):
    """위치가 없는 심볼은 적재에서 빠진다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [
            {"InfoType": "function", "Name": "HasPlace", "Namespace": ["SJH"],
             "Location": {"Filename": "core/a.cpp", "LineNumber": 3},
             "ReturnType": {"Name": "void"}, "Params": []},
            {"InfoType": "function", "Name": "NoPlace", "Namespace": ["SJH"],
             "ReturnType": {"Name": "void"}, "Params": []},
        ],
    })
    # 맹글링 파일 쪽도 같은 규칙이다 — 외부 라이브러리 타입이 이 꼴로 나온다
    _write(root, "GlobalNamespace/_ZTV7QWidget.json",
           {"InfoType": "record", "Name": "QWidget", "Namespace": ["GlobalNamespace"],
            "TagType": "class", "USR": "Q1"})
    names = {s["name"] for s in CD.load_clang_doc(root)}
    assert names == {"HasPlace"}


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_description_nested_text_is_flattened']"/>
# clang-doc의 주석 설명(Description)이 리스트 안에 리스트가 들어있는 중첩 구조로 오는데, 이걸 글자만 순서대로 이어붙여 한 줄 문자열로 만드는지 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 4. Description 은 리스트의 리스트다. 글자만 순서대로 이어 붙인다.
def test_description_nested_text_is_flattened(tmp_path: Path):
    """중첩된 TextComment 를 한 줄로 편다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "BroadcastChannels", "Namespace": ["Utils", "Core", "SJH"],
            "Location": {"Filename": "core/utils/channelutils.cpp", "LineNumber": 8},
            "ReturnType": {"Name": "void"}, "Params": [],
            "Description": {"HasParagraphComments": True, "ParagraphComments": [[
                {"TextComment": " 1채널을 3채널로 편다"},
                {"TextComment": " - 값이 같다."},
            ]]},
        }],
    })
    assert _by_name(CD.load_clang_doc(root), "BroadcastChannels")["doc"] == "1채널을 3채널로 편다 - 값이 같다."


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_description_absent_gives_empty_doc']"/>
# 주석이 아예 없는 함수라면 doc 필드가 비어 있는 문자열이어야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
def test_description_absent_gives_empty_doc(tmp_path: Path):
    """주석이 없으면 doc 은 빈 문자열이다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "Bare", "Namespace": ["SJH"],
            "Location": {"Filename": "core/a.cpp", "LineNumber": 1},
            "ReturnType": {"Name": "void"}, "Params": [],
        }],
    })
    assert _by_name(CD.load_clang_doc(root), "Bare")["doc"] == ""


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_records_come_from_mangled_files_not_index']"/>
# 레코드(클래스/구조체 등)의 위치 정보는 index.json이 아니라 이름이 맹글링된 별도 파일에만 들어있다는 사실을 확인하는 테스트다. index.json의 Records 항목은 이름과 USR만 있는 얕은 참조일 뿐이다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 5. 레코드의 위치는 index.json 이 아니라 맹글링 파일에만 있다.
def test_records_come_from_mangled_files_not_index(tmp_path: Path):
    """레코드의 위치·종류·네임스페이스는 맹글링 파일에서 온다."""
    root = str(tmp_path)
    # index.json 의 Records 는 이름과 USR 뿐인 얕은 참조다 — 여기엔 Location 이 없다
    _write(root, "SJH/index.json", {
        "Records": [{"Name": "SessionStore", "QualName": "SessionStore",
                     "USR": "S1", "DocumentationFileName": "_ZTVN3SJH12SessionStoreE"}],
    })
    _write(root, "SJH/_ZTVN3SJH12SessionStoreE.json", {
        "InfoType": "record", "Name": "SessionStore", "Namespace": ["Server", "SJH"],
        "TagType": "struct", "USR": "S1",
        "Location": {"Filename": "server/sessionstore.h", "LineNumber": 17},
    })
    syms = CD.load_clang_doc(root)
    rec = _by_name(syms, "SessionStore")     # 한 번만 나온다 — 참조와 파일을 겹쳐 세지 않는다
    assert rec["file"] == "server/sessionstore.h"
    assert rec["line"] == 17
    assert rec["kind"] == "struct"
    assert rec["namespace"] == "SJH::Server"


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_enum_kind_and_location_come_from_index']"/>
# 레코드와 달리 enum은 위치 정보가 index.json 안에 함께 실려서 온다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
def test_enum_kind_and_location_come_from_index(tmp_path: Path):
    """enum 은 index.json 에 위치가 함께 실려 온다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Enums": [{
            "InfoType": "enum", "Name": "E_MOTION_MODEL", "Namespace": ["Panorama", "Core", "SJH"],
            "Location": {"Filename": "core/panorama/alignment.h", "LineNumber": 18}, "USR": "E1",
        }],
    })
    sym = _by_name(CD.load_clang_doc(root), "E_MOTION_MODEL")
    assert sym["kind"] == "enum"
    assert (sym["file"], sym["line"]) == ("core/panorama/alignment.h", 18)


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_function_signature_has_return_type_and_params']"/>
# 함수의 반환 타입과 매개변수를 사람이 읽기 좋은 한 줄짜리 시그니처 문자열로 조립하는지 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 6. 시그니처
def test_function_signature_has_return_type_and_params(tmp_path: Path):
    """반환형과 인자를 사람이 읽는 한 줄로 만든다."""
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "ApplyHomography", "Namespace": ["SJH"],
            "Location": {"Filename": "core/panorama/homography.cpp", "LineNumber": 7},
            "ReturnType": {"Name": "bool"},
            "Params": [
                {"Name": "image", "Type": {"Name": "const cv::Mat &"}},
                {"Name": "dst", "Type": {"Name": "cv::Mat3b &"}},
            ],
        }],
    })
    sig = _by_name(CD.load_clang_doc(root), "ApplyHomography")["signature"]
    assert sig == "bool ApplyHomography(const cv::Mat & image, cv::Mat3b & dst)"


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_record_has_no_signature']"/>
# 레코드(클래스 등)는 함수가 아니라서 시그니처라는 개념이 없으니 signature 필드가 빈 문자열이어야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.test_clang_doc._by_name, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
def test_record_has_no_signature(tmp_path: Path):
    """레코드에는 시그니처가 없다."""
    root = str(tmp_path)
    _write(root, "R.json", {
        "InfoType": "record", "Name": "Session", "Namespace": ["SJH"], "TagType": "class",
        "USR": "R1", "Location": {"Filename": "server/s.h", "LineNumber": 4},
    })
    assert _by_name(CD.load_clang_doc(root), "Session")["signature"] == ""


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_duplicate_usr_is_collapsed_and_order_is_deterministic']"/>
# 같은 USR(고유 식별자)을 가진 심볼이 여러 파일에 중복으로 나타나도 결과에는 한 번만 나오고, 몇 번을 다시 읽어도 항상 같은 순서로 나와야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 7. 중복과 결정론
def test_duplicate_usr_is_collapsed_and_order_is_deterministic(tmp_path: Path):
    """같은 USR 은 한 번만 나오고, 두 번 읽어도 순서가 같다."""
    root = str(tmp_path)
    body = {"InfoType": "record", "Name": "Dup", "Namespace": ["SJH"], "TagType": "class",
            "USR": "SAME", "Location": {"Filename": "a.h", "LineNumber": 1}}
    _write(root, "x/_ZTV3Dup.json", body)
    _write(root, "y/_ZTV3Dup.json", dict(body))
    syms = CD.load_clang_doc(root)
    assert [s["name"] for s in syms] == ["Dup"]
    assert CD.load_clang_doc(root) == syms


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_accepts_the_parent_directory_of_json']"/>
# clang-doc이 `--output <D>` 옵션을 주면 실제로는 `<D>/json/` 폴더에 결과를 쓰는데, 적재기가 `<D>`와 `<D>/json` 둘 중 어느 경로를 줘도 똑같이 읽어야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.test_clang_doc._write, machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
# ── 8. 경로 편의 — clang-doc 은 `--output <D>` 에 `<D>/json/` 을 만든다. 둘 다 받는다.
def test_accepts_the_parent_directory_of_json(tmp_path: Path):
    """`<D>` 와 `<D>/json` 둘 다 적재 뿌리로 받는다."""
    root = str(tmp_path)
    _write(root, "json/index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "Inner", "Namespace": ["SJH"],
            "Location": {"Filename": "a.cpp", "LineNumber": 1},
            "ReturnType": {"Name": "void"}, "Params": [],
        }],
    })
    assert [s["name"] for s in CD.load_clang_doc(root)] == ["Inner"]
    assert [s["name"] for s in CD.load_clang_doc(os.path.join(root, "json"))] == ["Inner"]


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_missing_directory_gives_empty_list']"/>
# 존재하지 않는 폴더 경로를 줘도 프로그램이 에러로 죽지 않고 그냥 빈 목록을 돌려줘야 한다는 걸 확인하는 테스트다.
# 쓰는 것: machine.clang_doc.load_clang_doc · 쓰이는 곳: 없음
def test_missing_directory_gives_empty_list(tmp_path: Path):
    """없는 디렉토리를 주면 터지지 않고 빈 목록이다."""
    assert CD.load_clang_doc(os.path.join(str(tmp_path), "없는곳")) == []


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc._golden']"/>
# 가짜로 만든 데이터가 아니라 실제 C++ 저장소에서 clang-doc이 만들어낸 진짜 산출물을 읽어오는, 뒤이은 골든 테스트들이 공유하는 준비 함수다.
# 쓰는 것: machine.clang_doc.load_clang_doc · 쓰이는 곳: machine.test_clang_doc.test_golden_author_comments_are_carried, machine.test_clang_doc.test_golden_compute_panorama_is_located, machine.test_clang_doc.test_golden_counts, machine.test_clang_doc.test_golden_every_symbol_has_a_location
# ── 9. 골든 — 실제 저장소 산출물. 합성 데이터만으로 검증하지 않는다.
def _golden() -> list[Symbol]:
    d = os.path.join(WIKI_CPP_REPO, "out/codegraph-raw/clangdoc")
    if not os.path.isdir(os.path.join(d, "json")):
        pytest.skip(f"산출물 없음: {d}/json  (report-wiki prep 을 먼저 돌린다)")
    return CD.load_clang_doc(d)


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_golden_compute_panorama_is_located']"/>
# clang-doc 이 실제 C++ 저장소를 읽었을 때 자유 함수 하나(ComputePanorama)의 위치와 이름공간을 제대로 잡는지 확인하는 시험이다.
# 쓰는 것: machine.test_clang_doc._golden, machine.test_clang_doc._by_name · 쓰이는 곳: 없음
def test_golden_compute_panorama_is_located():
    """자유 함수가 파일:줄과 함께 잡히는지를 실제 산출물에서 본다."""
    sym = _by_name(_golden(), "ComputePanorama")
    assert (sym["file"], sym["line"]) == ("core/panorama/panorama.cpp", 129)
    assert sym["kind"] == "function"
    assert sym["namespace"] == "SJH::Core::Panorama"


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_golden_counts']"/>
# 실제 C++ 저장소를 clang-doc 으로 읽었을 때 나오는 심볼 종류별 개수를 못박아 두는 회귀 시험이다.
# 쓰는 것: machine.test_clang_doc._golden · 쓰이는 곳: 없음
def test_golden_counts():
    """종류별 개수를 못박는다 — 의도한 변경이면 기대값을 함께 고친다."""
    syms = _golden()
    kinds: dict[str, int] = {}
    for s in syms:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    assert kinds.get("function") == 236
    assert kinds.get("enum") == 4
    # 위치가 없는 외부 라이브러리 타입은 여기서 빠진다.
    assert kinds.get("class", 0) + kinds.get("struct", 0) + kinds.get("union", 0) == 71


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_golden_every_symbol_has_a_location']"/>
# 실제 저장소에서 읽어온 심볼마다 파일과 줄 번호가 반드시 있는지 확인하는 시험이다.
# 쓰는 것: machine.test_clang_doc._golden · 쓰이는 곳: 없음
def test_golden_every_symbol_has_a_location():
    """위치 없는 심볼이 새면 전수조사 레코드의 `where` 가 빈다."""
    for s in _golden():
        assert s["file"] and s["line"], s


# <include file="machine/comments.xml" path="//term[@id='machine.test_clang_doc.test_golden_author_comments_are_carried']"/>
# clang-uml 이 주지 못하는 저자 문서 주석(doc 필드)이 clang-doc 경로로는 실제로 실려 오는지 확인하는 시험이다.
# 쓰는 것: machine.test_clang_doc._golden, machine.test_clang_doc._by_name · 쓰이는 곳: 없음
def test_golden_author_comments_are_carried():
    """저자 문서 주석이 심볼에 실린다 — clang-uml 이 주지 못하는 값이다."""
    syms = _golden()
    assert sum(1 for s in syms if s["doc"]) >= 60
    assert "채널" in _by_name(syms, "BroadcastChannels")["doc"]
