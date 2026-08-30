"""test_clang_doc.py — clang-doc 산출물 적재기의 회귀 테스트.

**왜 필요한가.** `clang_doc.py` 가 읽는 형식에는 **틀려도 오류가 나지 않는 자리가 다섯**이다.
조용히 빈 값이나 뒤집힌 값을 내고 파이프라인 끝까지 통과한다.

  1. Namespace 역순   clang-doc 은 `["Panorama","Core","SJH"]` 로 준다. 안쪽부터다.
                      그대로 이으면 `Panorama::Core::SJH` 가 되어 1차 판정의 네임스페이스
                      허용목록(`CPP_FIRST_PARTY_NS`)이 통째로 빗나간다.
  2. Location 부재    Qt 의 QWidget 처럼 위치가 없는 요소가 섞여 나온다. 버려야 한다 —
                      위치 없는 노드는 `where` 가 비어 전수조사 레코드를 만들 수 없다.
  3. Description 중첩 저자 주석이 리스트의 리스트 안 `TextComment` 로 흩어져 있다.
  4. Records 는 얕다  **index.json 의 `Records` 배열에는 Location 이 없다.** 이름과 USR 뿐인
                      참조다. 실제 위치·상속·멤버는 맹글링된 개별 파일에 있다.
                      🔵 2026-08-29 QtVisionEdit 실측 — index.json 의 record 참조 64개는
                      **전량이 Location 없음**이었다. index.json 만 훑으면 클래스가 0개가 된다.
  5. GlobalNamespace  전역 네임스페이스를 `"GlobalNamespace"` 라는 **가짜 이름**으로 준다.
                      그대로 두면 `GlobalNamespace::MainWindow` 가 된다.

합성 데이터만으로 검증하지 않는다 — 아래 골든 테스트는 **실제 저장소 산출물**을 쓴다
(있을 때만 돌고, 없으면 skip).

  python -m pytest machine/test_clang_doc.py -q      # .venv 를 켠 뒤
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clang_doc as CD  # noqa: E402

# ⚠ 이름 함정 — `test_normalize.py` 의 `CPP_REPO` 상수는 환경변수 **`$GRAPHICS_REPO`** 를 읽는다
#   (C++ 골든 저장소). 여기서 쓰는 `$CPP_REPO` 는 **위키 대상**인 QtVisionEdit 으로 서로 다른
#   저장소다. 같은 낱말이 두 곳에서 다른 것을 가리키므로 이름을 달리 적는다.
WIKI_CPP_REPO = os.path.expandvars(os.environ.get("CPP_REPO", "")) or "/골든저장소_미지정/CPP_REPO"


def _write(root, rel, obj):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return path


def _by_name(syms, name):
    hits = [s for s in syms if s["name"] == name]
    assert len(hits) == 1, f"{name} 이 {len(hits)}개다"
    return hits[0]


# ── 1. 함정 ① — Namespace 는 안쪽부터 온다. 뒤집어 이어야 한다.
def test_namespace_is_reversed(tmp_path):
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


# ── 2. 함정 ⑤ — GlobalNamespace 는 이름이 아니라 "없음" 이다.
def test_global_namespace_becomes_empty(tmp_path):
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "main", "Namespace": ["GlobalNamespace"],
            "Location": {"Filename": "app/gui.cpp", "LineNumber": 39},
            "ReturnType": {"Name": "int"}, "Params": [],
        }],
    })
    assert _by_name(CD.load_clang_doc(root), "main")["namespace"] == ""


# ── 3. 함정 ② — Location 이 없는 요소는 버린다.
def test_symbol_without_location_is_dropped(tmp_path):
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
    # 맹글링 파일 쪽도 같은 규칙이다 — Qt 의 QWidget 이 이 꼴로 나온다
    _write(root, "GlobalNamespace/_ZTV7QWidget.json",
           {"InfoType": "record", "Name": "QWidget", "Namespace": ["GlobalNamespace"],
            "TagType": "class", "USR": "Q1"})
    names = {s["name"] for s in CD.load_clang_doc(root)}
    assert names == {"HasPlace"}


# ── 4. 함정 ③ — Description 은 리스트의 리스트다. 글자만 순서대로 이어 붙인다.
def test_description_nested_text_is_flattened(tmp_path):
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


def test_description_absent_gives_empty_doc(tmp_path):
    root = str(tmp_path)
    _write(root, "index.json", {
        "Functions": [{
            "InfoType": "function", "Name": "Bare", "Namespace": ["SJH"],
            "Location": {"Filename": "core/a.cpp", "LineNumber": 1},
            "ReturnType": {"Name": "void"}, "Params": [],
        }],
    })
    assert _by_name(CD.load_clang_doc(root), "Bare")["doc"] == ""


# ── 5. 함정 ④ — 레코드의 위치는 index.json 이 아니라 맹글링 파일에만 있다.
def test_records_come_from_mangled_files_not_index(tmp_path):
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


def test_enum_kind_and_location_come_from_index(tmp_path):
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


# ── 6. 시그니처 — 반환형과 인자를 사람이 읽는 한 줄로 만든다.
def test_function_signature_has_return_type_and_params(tmp_path):
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


def test_record_has_no_signature(tmp_path):
    root = str(tmp_path)
    _write(root, "R.json", {
        "InfoType": "record", "Name": "Session", "Namespace": ["SJH"], "TagType": "class",
        "USR": "R1", "Location": {"Filename": "server/s.h", "LineNumber": 4},
    })
    assert _by_name(CD.load_clang_doc(root), "Session")["signature"] == ""


# ── 7. 같은 USR 은 한 번만. 결정론 — 두 번 읽어도 같은 순서다.
def test_duplicate_usr_is_collapsed_and_order_is_deterministic(tmp_path):
    root = str(tmp_path)
    body = {"InfoType": "record", "Name": "Dup", "Namespace": ["SJH"], "TagType": "class",
            "USR": "SAME", "Location": {"Filename": "a.h", "LineNumber": 1}}
    _write(root, "x/_ZTV3Dup.json", body)
    _write(root, "y/_ZTV3Dup.json", dict(body))
    syms = CD.load_clang_doc(root)
    assert [s["name"] for s in syms] == ["Dup"]
    assert CD.load_clang_doc(root) == syms


# ── 8. 경로 편의 — clang-doc 은 `--output <D>` 에 `<D>/json/` 을 만든다. 둘 다 받는다.
def test_accepts_the_parent_directory_of_json(tmp_path):
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


def test_missing_directory_gives_empty_list(tmp_path):
    assert CD.load_clang_doc(os.path.join(str(tmp_path), "없는곳")) == []


# ── 9. 골든 — 실제 저장소 산출물. 합성 데이터만으로 검증하지 않는다.
def _golden():
    d = os.path.join(WIKI_CPP_REPO, "out/codegraph-raw/clangdoc")
    if not os.path.isdir(os.path.join(d, "json")):
        pytest.skip(f"산출물 없음: {d}/json  (report-wiki prep 을 먼저 돌린다)")
    return CD.load_clang_doc(d)


def test_golden_compute_panorama_is_located():
    """핸드오프가 못박은 좌표. 자유 함수가 파일:줄과 함께 잡히는지가 이 작업의 전부다."""
    sym = _by_name(_golden(), "ComputePanorama")
    assert (sym["file"], sym["line"]) == ("core/panorama/panorama.cpp", 129)
    assert sym["kind"] == "function"
    assert sym["namespace"] == "SJH::Core::Panorama"


def test_golden_counts():
    """수치가 바뀌면 무언가 변한 것이다 — 의도한 변경이면 이 기대값을 함께 고친다."""
    syms = _golden()
    kinds = {}
    for s in syms:
        kinds[s["kind"]] = kinds.get(s["kind"], 0) + 1
    assert kinds.get("function") == 236
    assert kinds.get("enum") == 4
    # 레코드 76개 중 Location 이 없는 Qt 타입 5개(QTimer·QHttpServer·QWidget·QWebSocket·
    # QNetworkAccessManager)가 빠져 71개다.
    assert kinds.get("class", 0) + kinds.get("struct", 0) + kinds.get("union", 0) == 71


def test_golden_every_symbol_has_a_location():
    """위치 없는 심볼이 새면 전수조사 레코드의 `where` 가 빈다."""
    for s in _golden():
        assert s["file"] and s["line"], s


def test_golden_author_comments_are_carried():
    """저자 문서 주석이 실려야 한다 — clang-uml 이 못 주던 것이 이 작업의 이득 절반이다."""
    syms = _golden()
    assert sum(1 for s in syms if s["doc"]) >= 60
    assert "채널" in _by_name(syms, "BroadcastChannels")["doc"]
