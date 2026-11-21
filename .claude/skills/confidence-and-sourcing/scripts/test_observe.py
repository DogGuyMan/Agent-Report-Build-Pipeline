#!/usr/bin/env python3
"""observe.py 의 시험. 표준 라이브러리만 쓴다.

    python3 test_observe.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import observe as O  # noqa: E402

SCRIPT = os.path.join(HERE, "observe.py")


class Repo(unittest.TestCase):
    """파일 몇 개가 든 임시 저장소와 그 위의 세션 기억 하나."""

    limit = 100

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.write("src/a.py", "one\ntwo\nthree\nfour\nfive\n")
        self.write("src/b.py", "alpha\nrequireAuth()\n")
        self.ctx = O.Context(self.root, limit=self.limit)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def p(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def write(self, rel: str, body: str) -> None:
        os.makedirs(os.path.dirname(self.p(rel)), exist_ok=True)
        with open(self.p(rel), "w", encoding="utf-8") as f:
            f.write(body)

    def last(self) -> dict:
        return self.ctx.events[-1]


class Immediate(Repo):
    def test_read_returns_the_lines_and_records_what_was_seen(self) -> None:
        """본 범위와 그때의 파일 해시는 세션이 든다. LLM 이 외울 것이 아니다."""
        reply = self.ctx.read(self.p("src/a.py"), "2-3")
        self.assertEqual(reply.code, 0)
        self.assertIn("2\ttwo", reply.text)
        self.assertNotIn("four", reply.text)
        e = self.last()
        self.assertEqual((e["kind"], e["path"], e["lines"], e["total"], e["shown"]), ("read", "src/a.py", [2, 3], 5, True))
        self.assertIn("two", e["output"])
        with open(self.p("src/a.py"), "rb") as f:
            self.assertEqual(e["sha256"], hashlib.sha256(f.read()).hexdigest())

    def test_grep_returns_the_hits_and_records_how_much_it_searched(self) -> None:
        """훑은 범위가 남아야 0건이 "없다" 인지 "덜 봤다" 인지 가른다."""
        reply = self.ctx.grep("requireAuth", [self.p("src")])
        self.assertIn("src/b.py:2: requireAuth()", reply.text)
        e = self.last()
        self.assertEqual((e["kind"], e["count"], e["scanned"], e["hits"]), ("grep", 1, 2, [["src/b.py", 2]]))

    def test_grep_with_no_hit_is_still_recorded(self) -> None:
        """못 찾은 검색도 쌓는다. 지우면 찾아봤다는 사실이 사라진다."""
        self.assertEqual(self.ctx.grep("nothing_here", [self.p("src")]).code, 0)
        self.assertEqual((self.last()["kind"], self.last()["count"]), ("grep", 0))

    def test_run_returns_the_output_and_passes_the_exit_code(self) -> None:
        """명령 · 종료 코드 · 출력 전문은 세션이 든다."""
        reply = self.ctx.run("echo hello && exit 3", self.root)
        self.assertEqual(reply.code, 3)
        self.assertIn("hello", reply.text)
        e = self.last()
        self.assertEqual((e["kind"], e["command"], e["exit"], e["lines"], e["output"]),
                         ("run", "echo hello && exit 3", 3, 1, "hello"))

    def test_read_of_a_missing_file_is_recorded_as_a_miss(self) -> None:
        """없는 파일을 열어 본 것도 관찰이다."""
        self.assertEqual(self.ctx.read(self.p("src/gone.py")).code, 1)
        self.assertEqual((self.last()["path"], self.last()["missing"]), ("src/gone.py", True))

    def test_every_reply_says_how_many_tries_are_used(self) -> None:
        """남은 횟수가 답에 보여야 상한에 닿기 전에 찾을 것을 고른다."""
        self.assertIn("[1/100]", self.ctx.read(self.p("src/a.py"), "1").text)
        self.assertIn("[2/100]", self.ctx.grep("alpha", [self.p("src")]).text)
        self.assertIn("[3/100]", self.ctx.run("true", self.root).text)


class Deferred(Repo):
    def test_a_deferred_call_answers_in_one_line_and_keeps_the_output(self) -> None:
        """모아 보기는 출력을 세션에 쌓아 두고 확인 한 줄만 돌려준다."""
        reply = self.ctx.read(self.p("src/a.py"), "2-3", defer=True)
        self.assertNotIn("\n", reply.text)
        self.assertNotIn("two", reply.text)
        self.assertEqual(self.last()["shown"], False)
        self.assertIn("two", self.last()["output"])

    def test_show_returns_everything_not_yet_seen_and_only_once(self) -> None:
        """한 번 받은 출력을 다시 쏟으면 모아 보는 뜻이 없다."""
        self.ctx.read(self.p("src/a.py"), "2-3", defer=True)
        self.ctx.run("echo now", self.root)
        self.ctx.grep("requireAuth", [self.p("src")], defer=True)
        shown = self.ctx.show().text
        self.assertIn("2\ttwo", shown)
        self.assertIn("src/b.py:2: requireAuth()", shown)
        self.assertNotIn("now", shown)
        self.assertTrue(all(e["shown"] for e in self.ctx.events))
        self.assertIn("없다", self.ctx.show().text)

    def test_show_names_what_each_output_came_from(self) -> None:
        """여러 출력을 한꺼번에 받으면 어느 것이 어느 호출의 것인지가 같이 와야 한다."""
        self.ctx.read(self.p("src/a.py"), "2-3", defer=True)
        self.ctx.run("echo later", self.root, defer=True)
        shown = self.ctx.show().text
        self.assertIn("E1 read src/a.py:2-3", shown)
        self.assertIn("E2 run", shown)
        self.assertIn("echo later", shown)

    def test_show_of_one_event_returns_it_again_after_it_was_seen(self) -> None:
        """대화가 앞의 출력을 잊었을 때 다시 돌리지 않고 다시 받는다."""
        self.ctx.read(self.p("src/a.py"), "2-3")
        self.assertIn("2\ttwo", self.ctx.show(1).text)

    def test_show_of_an_event_that_does_not_exist_is_an_error(self) -> None:
        """없는 번호에 빈 답을 주면 출력이 없었던 것으로 읽힌다."""
        self.assertEqual(self.ctx.show(9).code, 2)

    def test_a_deferred_run_still_says_how_it_ended(self) -> None:
        """출력은 미뤄도 실패했는지는 그 자리에서 알아야 한다."""
        reply = self.ctx.run("echo hello && exit 3", self.root, defer=True)
        self.assertEqual(reply.code, 3)
        self.assertIn("exit 3", reply.text)
        self.assertIn("1줄", reply.text)
        self.assertNotIn("hello", reply.text)

    def test_a_deferred_grep_still_says_how_many_it_found(self) -> None:
        """0건이면 출력을 받을 필요가 없다. 건수는 확인 줄에 온다."""
        self.assertIn("1건", self.ctx.grep("requireAuth", [self.p("src")], defer=True).text)

    def test_status_counts_the_outputs_not_yet_seen(self) -> None:
        """받지 않은 출력이 남았는지는 세션이 센다."""
        self.ctx.read(self.p("src/a.py"), "1", defer=True)
        self.ctx.read(self.p("src/a.py"), "2")
        self.assertIn("안 본 출력 1건", self.ctx.status().text)


class Reread(Repo):
    def test_lines_already_seen_are_shown_again_with_a_notice(self) -> None:
        """다시 읽으면 다시 보여 준다 — 내용이 필요해서 부른 것이다. 이미 봤다는 사실만 덧붙인다."""
        self.ctx.read(self.p("src/a.py"), "1-3")
        reply = self.ctx.read(self.p("src/a.py"), "2-3")
        self.assertIn("이미 봄(E1)", reply.text)
        self.assertIn("2\ttwo", reply.text)
        self.assertEqual(self.ctx.calls, 2)

    def test_no_notice_when_the_file_changed_since(self) -> None:
        """바뀐 파일의 같은 줄 번호는 본 적 없는 내용이다."""
        self.ctx.read(self.p("src/a.py"), "1-3")
        self.write("src/a.py", "zero\none\ntwo\nthree\n")
        self.assertNotIn("이미 봄", self.ctx.read(self.p("src/a.py"), "2-3").text)

    def test_no_notice_when_some_of_the_lines_are_new(self) -> None:
        """일부만 본 범위를 "이미 봤다" 고 하면 안 본 줄까지 본 것으로 읽힌다."""
        self.ctx.read(self.p("src/a.py"), "1-2")
        self.assertNotIn("이미 봄", self.ctx.read(self.p("src/a.py"), "2-4").text)


class Tries(Repo):
    limit = 3

    def use_up(self) -> None:
        self.ctx.read(self.p("src/a.py"), "1")
        self.ctx.grep("alpha", [self.p("src")])
        self.ctx.run("true", self.root)

    def test_a_call_past_the_limit_is_refused_and_not_recorded(self) -> None:
        """상한은 끝없이 찾는 것을 멈추는 장치다. 넘겨서 본 것이 쌓이면 상한이 없는 것과 같다."""
        self.use_up()
        for reply in (self.ctx.read(self.p("src/a.py"), "2"), self.ctx.grep("one", [self.p("src")]),
                      self.ctx.run("true", self.root)):
            self.assertEqual(reply.code, 3)
            self.assertIn("more", reply.text)
        self.assertEqual((len(self.ctx.events), self.ctx.calls, self.ctx.refused), (3, 3, 3))

    def test_a_call_that_fails_still_uses_up_a_try(self) -> None:
        """시도는 부른 횟수다. 틀린 정규식이나 파일 끝을 넘는 읽기가 공짜면 상한 밖에서 얼마든지 찔러본다."""
        self.assertEqual(self.ctx.handle("grep", {"pattern": "(", "paths": [self.p("src")]}).code, 2)
        self.assertEqual(self.ctx.handle("read", {"path": self.p("src/a.py"), "lines": "99"}).code, 1)
        self.assertEqual(self.ctx.events, [])
        self.assertIn("[3/3]", self.ctx.read(self.p("src/a.py"), "1").text)

    def test_more_grants_tries_and_the_grant_is_recorded(self) -> None:
        """더 찾으려면 횟수를 따로 받아야 한다. 언제 얼마를 받았는지는 세션이 적는다."""
        self.use_up()
        self.assertEqual(self.ctx.read(self.p("src/a.py"), "2").code, 3)
        self.assertEqual(self.ctx.more(2).code, 0)
        self.assertIn("[4/5]", self.ctx.read(self.p("src/a.py"), "2").text)
        self.assertEqual([g["more"] for g in self.ctx.grants], [2])

    def test_show_and_check_are_not_tries(self) -> None:
        """상한은 찾는 횟수에 건다. 이미 본 것을 다시 받거나 글을 대조하는 일은 막지 않는다."""
        self.use_up()
        self.write("plans/x.md", "- 가 🔵 92 — src/a.py:1\n")
        self.assertEqual(self.ctx.show(1).code, 0)
        self.assertEqual(self.ctx.check(self.p("plans/x.md")).code, 0)
        self.assertEqual(self.ctx.calls, 3)


class Check(Repo):
    PLAN = "- 재사용한다 🔵 92 — src/a.py:2\n- 호출한다 🔵 90 — src/b.py:2\n"

    def test_reports_citations_this_session_never_read(self) -> None:
        """글에 적힌 인용이 실재해도, 이 세션이 그 줄을 본 적이 없으면 읽고 쓴 인용이 아니다."""
        self.write("plans/auth.md", self.PLAN)
        self.ctx.read(self.p("src/a.py"))
        reply = self.ctx.check(self.p("plans/auth.md"))
        self.assertEqual(reply.code, 0)
        self.assertIn("src/b.py:2", reply.text)
        e = self.last()
        self.assertEqual((e["kind"], e["file"], e["unread"]), ("check", "plans/auth.md", ["src/b.py:2"]))
        self.assertEqual(e["citations"], {"total": 2, "found": 2, "observed": 1})

    def test_a_grep_hit_counts_as_having_seen_that_line(self) -> None:
        """grep 이 보여 준 줄은 본 줄이다."""
        self.write("plans/auth.md", self.PLAN)
        self.ctx.read(self.p("src/a.py"))
        self.ctx.grep("requireAuth", [self.p("src")])
        self.ctx.check(self.p("plans/auth.md"))
        self.assertEqual(self.last()["unread"], [])

    def test_a_citation_into_a_file_changed_after_reading_is_stale(self) -> None:
        """읽은 뒤 바뀐 파일의 줄 번호는 다른 내용을 가리킬 수 있다."""
        self.write("plans/auth.md", "- 재사용한다 🔵 92 — src/a.py:2\n")
        self.ctx.read(self.p("src/a.py"))
        self.write("src/a.py", "zero\none\ntwo\n")
        self.ctx.check(self.p("plans/auth.md"))
        self.assertEqual(self.last()["stale"], ["src/a.py:2"])

    def test_number_above_100_in_the_document_fails_the_check(self) -> None:
        """한 번 부르는 검사기와 같은 수위다 — 0–100 밖의 정수만 실패다."""
        self.write("plans/bad.md", "결정 🔵 999\n")
        self.assertEqual(self.ctx.check(self.p("plans/bad.md")).code, 1)


class Memory(Repo):
    limit = 5

    def test_a_reloaded_context_keeps_what_was_seen_and_what_is_still_unseen(self) -> None:
        """프로세스가 죽었다 살아나도 본 줄과 아직 받지 않은 출력은 그대로여야 한다."""
        self.ctx.read(self.p("src/a.py"), "1-3", defer=True)
        self.ctx.handle("grep", {"pattern": "(", "paths": []})
        self.ctx.more(4)
        again = O.Context.load(json.loads(json.dumps(self.ctx.dump())))
        self.assertEqual((again.calls, again.limit, [g["more"] for g in again.grants]), (2, 9, [4]))
        self.assertIn("2\ttwo", again.show().text)
        self.write("plans/x.md", "- 가 🔵 92 — src/a.py:2\n")
        again.check(self.p("plans/x.md"))
        self.assertEqual(again.events[-1]["unread"], [])


class Session(unittest.TestCase):
    """명령줄로 부른다. 기억은 호출 사이에 파일로만 이어진다."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        os.makedirs(os.path.join(self.root, "src"))
        with open(os.path.join(self.root, "src", "a.py"), "w", encoding="utf-8") as f:
            f.write("one\ntwo\nthree\n")
        self.state = tempfile.TemporaryDirectory(prefix="ob")
        self.env = dict(os.environ, CONFIDENCE_SESSION_DIR=self.state.name, CONFIDENCE_SESSION_LIMIT="3")

    def tearDown(self) -> None:
        self.cli("end")
        self.tmp.cleanup()
        self.state.cleanup()

    def argv(self, *args: str) -> list[str]:
        return [sys.executable, SCRIPT, "--root", self.root, *args]

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(self.argv(*args), capture_output=True, text=True, env=self.env, cwd=self.root)

    def work_file(self) -> str:
        with mock.patch.dict(os.environ, {"CONFIDENCE_SESSION_DIR": self.state.name}):
            return O.session_paths(self.root)[0]

    def running(self) -> list[str]:
        found = subprocess.run(["pgrep", "-f", "observe.py --root %s" % self.root], capture_output=True, text=True)
        return found.stdout.split()

    def test_the_first_observation_starts_the_session_by_itself(self) -> None:
        """세션을 여는 일은 LLM 이 외울 절차가 아니다. 처음 본 순간에 상태 파일이 생긴다."""
        first = self.cli("read", "src/a.py", "1-3")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("1\tone", first.stdout)
        self.assertIn("사건 1개", self.cli("status").stdout)

    def test_no_process_is_left_running_between_calls(self) -> None:
        """기억은 파일에 있다. 호출이 끝나면 떠 있는 프로세스가 없어야 한다."""
        self.cli("read", "src/a.py", "1")
        self.assertEqual(self.running(), [])
        self.assertTrue(os.path.isfile(self.work_file()))
        self.assertIn("[2/3]", self.cli("read", "src/a.py", "2").stdout)

    def test_the_state_file_is_kept_outside_the_repository(self) -> None:
        """LLM 이 읽을 필요가 없는 파일이다. 저장소에 생기면 찾기 결과와 git 상태에 섞인다."""
        self.cli("read", "src/a.py", "1")
        self.assertEqual(os.listdir(self.root), ["src"])

    def test_the_state_file_is_readable_only_by_its_owner(self) -> None:
        """상태 파일에는 읽은 줄과 명령의 출력이 그대로 든다. 여럿이 쓰는 임시 폴더에서 남이 읽으면 안 된다."""
        self.cli("run", "echo secret")
        self.assertEqual(os.stat(self.work_file()).st_mode & 0o777, 0o600)

    def test_outputs_deferred_in_separate_calls_come_back_together(self) -> None:
        """기억이 파일로 이어져야, 따로 부른 호출들의 출력을 한 번에 받는다."""
        self.cli("read", "src/a.py", "1", "--defer")
        self.cli("grep", "two", "src", "--defer")
        shown = self.cli("show").stdout
        self.assertIn("1\tone", shown)
        self.assertIn("src/a.py:2: two", shown)
        self.assertIn("없다", self.cli("show").stdout)

    def test_show_without_a_session_fails_loudly(self) -> None:
        """세션이 없는데 빈 답을 주면 받을 출력이 없었던 것으로 읽힌다."""
        got = self.cli("show")
        self.assertEqual(got.returncode, 2)
        self.assertIn("세션이 없다", got.stderr)

    def test_end_leaves_a_json_file_with_the_outputs_and_closes_the_session(self) -> None:
        """끝내면 기억이 남길 자리로 옮겨지고, 상태 파일은 사라져 다음 관찰이 새 세션이 된다."""
        self.cli("read", "src/a.py", "1-3")
        self.cli("run", "echo ok")
        out = os.path.join(self.root, "auth.evidence.json")
        done = self.cli("end", "--out", out)
        self.assertEqual(done.returncode, 0)
        self.assertIn("auth.evidence.json", done.stdout)
        self.assertNotIn(self.root, done.stdout)
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual([e["kind"] for e in data["events"]], ["read", "run"])
        self.assertEqual(data["events"][1]["output"], "ok")
        self.assertTrue(data["ended_at"])
        self.assertEqual(self.cli("status").returncode, 2)
        self.assertFalse(os.path.exists(self.work_file()))

    def test_calls_made_at_the_same_time_all_land_in_the_file(self) -> None:
        """한 왕복에 관찰 셋을 나란히 부르면 셋이 같은 파일을 동시에 고친다. 하나도 덮여 사라지면 안 된다."""
        procs = [subprocess.Popen(self.argv("read", "src/a.py", str(n)), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, env=self.env, cwd=self.root) for n in (1, 2, 3)]
        for p in procs:
            p.communicate()
        self.assertEqual([p.returncode for p in procs], [0, 0, 0])
        self.assertIn("사건 3개 · 시도 3/3", self.cli("status").stdout)

    def test_a_session_left_unused_is_put_away_when_observing_starts_again(self) -> None:
        """끝내지 않고 둔 세션에 다음 날의 관찰이 이어 쌓이면 다른 일의 기록과 횟수가 섞인다."""
        self.cli("read", "src/a.py", "1")
        long_ago = time.time() - O.IDLE_SECONDS - 60
        os.utime(self.work_file(), (long_ago, long_ago))
        again = self.cli("read", "src/a.py", "2")
        self.assertIn("지난 세션", again.stdout)
        self.assertIn("[1/3]", again.stdout)
        kept = os.listdir(os.path.join(self.root, ".confidence"))
        self.assertEqual(len(kept), 1)
        with open(os.path.join(self.root, ".confidence", kept[0]), encoding="utf-8") as f:
            self.assertEqual([e["lines"] for e in json.load(f)["events"]], [[1, 1]])

    def test_an_unused_session_can_still_be_shown_and_ended(self) -> None:
        """오래 둔 세션이라도 받지 않은 출력을 받거나 끝내는 일은 그 세션에 해야 한다. 새로 보려 할 때만 치운다."""
        self.cli("read", "src/a.py", "1", "--defer")
        long_ago = time.time() - O.IDLE_SECONDS - 60
        os.utime(self.work_file(), (long_ago, long_ago))
        self.assertIn("1\tone", self.cli("show").stdout)

    def test_a_refused_session_goes_on_only_after_more_is_granted(self) -> None:
        """상한에 닿으면 멈추고, 횟수를 더 받은 뒤에만 잇는다."""
        for line in ("1", "2", "3"):
            self.cli("read", "src/a.py", line)
        self.assertEqual(self.cli("read", "src/a.py", "1").returncode, 3)
        self.assertEqual(self.cli("more", "1").returncode, 0)
        again = self.cli("read", "src/a.py", "1")
        self.assertEqual(again.returncode, 0)
        self.assertIn("[4/4]", again.stdout)

    def test_check_compares_a_document_with_what_the_session_saw(self) -> None:
        """다 쓴 글의 인용을 세션이 본 줄과 대조한다."""
        self.cli("read", "src/a.py", "1-3")
        with open(os.path.join(self.root, "auth.md"), "w", encoding="utf-8") as f:
            f.write("- 재사용한다 🔵 92 — src/a.py:2\n")
        self.assertIn("본 것 1건", self.cli("check", "auth.md").stdout)


if __name__ == "__main__":
    unittest.main()
