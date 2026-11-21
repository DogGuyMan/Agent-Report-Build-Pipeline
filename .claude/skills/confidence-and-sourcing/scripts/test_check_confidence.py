#!/usr/bin/env python3
"""check_confidence.py 의 시험. 표준 라이브러리만 쓴다.

    python3 test_check_confidence.py
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_confidence as C  # noqa: E402


def marks(text: str) -> list[tuple[int, str, object]]:
    return [(a.line, a.tier, C.MEASURED if a.measured else a.value) for a in C.find_anchors(text)]


class FindAnchors(unittest.TestCase):
    def test_reads_tier_and_number_with_or_without_a_space(self) -> None:
        """표기는 `🔵 92` 와 `🟡70` 둘 다 쓰인다 — 한쪽만 읽으면 절반을 검사하지 않는다."""
        self.assertEqual(marks("결정 🔵 92 — 근거\n| 표 | 🟡70 |\n판단 💭 40."),
                         [(1, "🔵", 92), (2, "🟡", 70), (3, "💭", 40)])

    def test_number_followed_by_a_date_or_a_counter_is_not_an_anchor(self) -> None:
        """`🔵 2026-11-04 실측` 의 2026 과 `🔵 11개` 의 11 은 확신도가 아니다 — 읽으면 멀쩡한 글이 실패한다."""
        self.assertEqual(marks("(🔵 2026-11-04 Mac 실측)\n🔵 11개 확인\n🔵 1.2 판"),
                         [(1, "🔵", None), (2, "🔵", None), (3, "🔵", None)])

    def test_a_band_written_as_a_range_is_not_an_anchor(self) -> None:
        """`🔵 90–100` 은 구간을 설명한 글이다. 90 을 확신도로 읽으면 규칙을 적은 문장마다 근거 인용 경고가 붙는다."""
        self.assertEqual(marks("구간(🔵 90–100 · 🟡 60-89 · 💭 0~59)"), [(1, "🔵", None), (1, "🟡", None), (1, "💭", None)])

    def test_reads_the_measured_label(self) -> None:
        """`🔵 실측` 은 숫자 없는 🔵 표기다. 근거 인용 검사의 대상이다."""
        self.assertEqual(marks("🔵 실측 — 명령 출력"), [(1, "🔵", C.MEASURED)])

    def test_skips_notation_inside_code(self) -> None:
        """코드 글꼴과 코드 블록 안의 표기는 쓰는 법을 보인 예시다. 주장이 아니다."""
        self.assertEqual(marks("예: `🔵 92`, `🟡 70`\n```\n💭 80\n```\n본문 🟡 70"), [(5, "🟡", 70)])


class Notation(unittest.TestCase):
    def check(self, text: str) -> C.Notation:
        return C.check_notation(C.find_anchors(text))

    def test_number_above_100_is_an_error(self) -> None:
        """0–100 밖의 정수는 어떤 뜻으로도 읽을 수 없다."""
        got = self.check("결정 🔵 999")
        self.assertEqual(got.out_of_range, ["1줄 🔵 999"])

    def test_number_outside_its_tier_band_is_a_warning(self) -> None:
        """티어는 증거 유형이 정하고 숫자는 그 구간 안에서만 움직인다. `💭 80` 은 어느 뜻으로도 성립하지 않는다."""
        got = self.check("🔵 85\n🟡 55\n💭 80")
        self.assertEqual(got.out_of_range, [])
        self.assertEqual(got.off_band, ["1줄 🔵 85", "2줄 🟡 55", "3줄 💭 80"])

    def test_both_edges_of_every_band_pass(self) -> None:
        """경계값 90 · 60 에서 하나 어긋나면 멀쩡한 표기에 경고가 붙는다."""
        got = self.check("🔵 90 🔵 100 🟡 60 🟡 89 💭 0 💭 59")
        self.assertEqual((got.out_of_range, got.off_band), ([], []))

    def test_bands_are_the_ones_the_skill_text_states(self) -> None:
        """구간의 정본은 SKILL.md 다. 스크립트의 것과 어긋나면 글대로 써도 경고가 뜬다."""
        with open(os.path.join(os.path.dirname(os.path.abspath(C.__file__)), "..", "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        for tier, (lo, hi) in C.BANDS.items():
            self.assertIn("%s %d–%d" % (tier, lo, hi), skill)


class Binding(unittest.TestCase):
    def missing(self, text: str) -> list[str]:
        return C.check_binding(text, C.find_anchors(text))

    def test_green_with_a_file_line_or_a_url_in_the_same_unit_passes(self) -> None:
        """🔵 는 인용을 붙여야 쓸 수 있는 티어다."""
        self.assertEqual(self.missing("- 재사용한다 🔵 92 — `src/a.py:12`\n- 문서 🔵 95 https://example.com/doc"), [])

    def test_citation_on_a_wrapped_line_of_the_same_item_counts(self) -> None:
        """목록 항목과 문단은 줄을 넘겨 쓴다. 다음 줄의 인용을 못 보면 멀쩡한 글에 경고가 붙는다."""
        self.assertEqual(self.missing("- 재사용한다 🔵 92 —\n  정의는 src/a.py:12 에 있다\n"), [])

    def test_markdown_link_to_a_line_counts(self) -> None:
        """`[이름](경로#L12)` 꼴 링크도 줄을 가리키는 인용이다."""
        self.assertEqual(self.missing("재사용한다 🔵 92 — [a.py](src/a.py#L12)"), [])

    def test_citation_in_another_item_or_table_row_does_not_count(self) -> None:
        """이웃 항목의 인용은 이 주장의 근거가 아니다."""
        self.assertEqual(self.missing("- 가 🔵 92\n- 나 src/a.py:12\n\n| 다 | 🔵 실측 |\n| 라 | src/a.py:12 |"),
                         ["1줄 🔵 92", "4줄 🔵 실측"])

    def test_only_anchored_green_needs_a_citation(self) -> None:
        """🟡 · 💭 와 숫자 없는 🔵 표지는 인용을 요구하는 티어가 아니다."""
        self.assertEqual(self.missing("통념 🟡 70\n판단 💭 40\n사실이다 🔵."), [])


class Citations(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, "src"))
        os.makedirs(os.path.join(self.root, "docs"))
        with open(os.path.join(self.root, "src", "a.py"), "w", encoding="utf-8") as f:
            f.write("one\ntwo\nthree\n")
        self.resolve = C.make_resolver(os.path.join(self.root, "docs"), self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def check(self, text: str) -> C.Citations:
        return C.check_citations(text, self.resolve)

    def test_counts_only_paths_with_a_line_number(self) -> None:
        """줄 번호 없는 경로는 이름을 부른 것이지 읽었다는 인용이 아니다 — 분모에 넣으면 비율이 부푼다."""
        got = self.check("src/a.py:2 와 src/a.py 와 terms-db.json")
        self.assertEqual((got.total, got.found), (1, 1))

    def test_reports_a_missing_file_and_a_line_past_the_end(self) -> None:
        """없는 파일과 없는 줄은 낡았거나 지어낸 인용이다. 0 번 줄과 끝을 넘는 범위도 같다."""
        got = self.check("src/gone.py:1 src/a.py:4 src/a.py:2-9 src/a.py:0")
        self.assertEqual(got.found, 0)
        self.assertEqual(got.missing, ["src/gone.py:1"])
        self.assertEqual(got.beyond, ["src/a.py:4", "src/a.py:2-9", "src/a.py:0"])

    def test_accepts_a_range_to_the_last_line_with_either_dash(self) -> None:
        """범위는 `1-3` 과 `1–3` 둘 다 쓰인다. 마지막 줄까지 닿는 범위는 실재한다."""
        got = self.check("src/a.py:1-3 src/a.py:2–3")
        self.assertEqual((got.total, got.found), (2, 2))

    def test_counts_each_citation_once(self) -> None:
        """같은 인용을 여러 번 적어 분모를 늘릴 수 없어야 한다."""
        self.assertEqual(self.check("src/a.py:2 다시 src/a.py:2").total, 1)

    def test_reads_a_markdown_link_target_instead_of_its_label(self) -> None:
        """`[a.py:2](src/a.py#L2)` 는 인용 하나다. 이름표의 `a.py:2` 를 따로 세면 같은 줄을 두 번 센다."""
        got = self.check("[a.py:2](../src/a.py#L2) 와 [끝](../src/a.py#L9)")
        self.assertEqual((got.total, got.found, got.beyond), (2, 1, ["../src/a.py#L9"]))

    def test_skips_citations_inside_fenced_code(self) -> None:
        """코드 블록 안의 `파일:줄` 은 예시나 명령 출력이다. 글쓴이의 인용이 아니다."""
        self.assertEqual(self.check("```\nsrc/gone.py:1\n```").total, 0)

    def test_finds_a_bare_file_name_when_git_tracks_exactly_one(self) -> None:
        """이름만 적은 인용은 저장소에 그 이름이 하나일 때만 그 파일이다."""
        git = ["git", "-C", self.root, "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(git + ["init", "-q"], check=True)
        subprocess.run(git + ["add", "-A"], check=True)
        resolve = C.make_resolver(os.path.join(self.root, "docs"), self.root)
        self.assertEqual(C.check_citations("a.py:2", resolve).found, 1)

    def test_expands_home_and_skips_an_unset_variable(self) -> None:
        """`$REPO/…` 처럼 변수로 적은 경로는 값이 없으면 판정할 수 없다. 없는 파일이라고 하지 않고 건너뛴다."""
        os.environ.pop("CC_ABSENT", None)
        os.environ["CC_ROOT"] = self.root
        try:
            got = self.check("$CC_ROOT/src/a.py:2 와 $CC_ABSENT/src/a.py:2")
        finally:
            del os.environ["CC_ROOT"]
        self.assertEqual((got.total, got.found, got.skipped), (1, 1, 1))


class Main(unittest.TestCase):
    def run_main(self, body: str, *extra: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plan.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = C.main([path, "--root", tmp, *extra])
            return code, out.getvalue()

    def test_exits_1_only_for_a_number_outside_0_to_100(self) -> None:
        """경고는 글쓴이가 판단할 일이고 실패는 표기 자체가 깨진 것이다. 둘을 종료 코드로 가른다."""
        self.assertEqual(self.run_main("결정 🔵 999 — plan.md:1")[0], 1)
        self.assertEqual(self.run_main("결정 💭 80")[0], 0)

    def test_says_what_passing_does_not_mean(self) -> None:
        """통과를 "확신도가 옳다" 로 읽으면 이 검사가 근거 없는 확신을 하나 더 만든다."""
        code, out = self.run_main("결정 🔵 92 — plan.md:1")
        self.assertEqual(code, 0)
        self.assertIn("확신도가 옳다는 뜻은 아니다", out)

    def test_tells_where_it_looked_when_a_cited_file_is_missing(self) -> None:
        """다른 저장소의 파일을 인용한 글은 뿌리를 잘못 잡으면 전부 없는 파일로 나온다 — 어디를 봤는지 알려야 고칠 수 있다."""
        code, out = self.run_main("근거 src/gone.py:1")
        self.assertEqual(code, 0)
        self.assertIn("파일이 없다: src/gone.py:1", out)
        self.assertIn("--root", out)


if __name__ == "__main__":
    unittest.main()
