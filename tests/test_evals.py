import os

from evals.cases import CASES
from evals.runner import run_case
from tests.fakes import FakeClient, text, tool_use


def case(name):
    return next(c for c in CASES if c.name == name)


def test_passing_case_and_cwd_restored():
    before = os.getcwd()
    client = FakeClient([
        ([tool_use("t1", "write_file", path="hello.txt", content="bonjour")], "tool_use"),
        ([text("fait")], "end_turn"),
    ])
    r = run_case(client, case("write_file"))
    assert r["passed"] and r["error"] is None
    assert os.getcwd() == before


def test_failing_case():
    r = run_case(FakeClient([([text("je ne fais rien")], "end_turn")]), case("write_file"))
    assert not r["passed"]


def test_answer_based_case():
    r = run_case(FakeClient([([text("Le port est 8421.")], "end_turn")]), case("read_config"))
    assert r["passed"]


def test_api_error_is_a_failed_case_not_a_crash():
    class Boom(FakeClient):
        def stream(self, **kw):
            raise RuntimeError("panne")

    r = run_case(Boom([]), case("write_file"))
    assert not r["passed"] and "panne" in r["error"]


def test_fix_bug_check_detects_buggy_and_fixed(tmp_path):
    c = case("fix_bug")
    c.setup(tmp_path)
    assert not c.check(tmp_path, "")
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a + b\n")
    assert c.check(tmp_path, "")
