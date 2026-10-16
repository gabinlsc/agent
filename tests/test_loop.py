from agent.loop import run
from agent.tools import TOOLS, default_handlers
from tests.fakes import FakeClient, text, tool_use


def test_loop_executes_tool_then_answers(tmp_path):
    target = tmp_path / "a.txt"
    client = FakeClient([
        ([tool_use("t1", "write_file", path=str(target), content="salut")], "tool_use"),
        ([text("fait")], "end_turn"),
    ])
    messages = [{"role": "user", "content": "écris"}]
    out = run(client, messages, TOOLS, default_handlers(lambda c: False))
    assert out == "fait"
    assert target.read_text() == "salut"
    result = messages[2]["content"][0]
    assert result["tool_use_id"] == "t1" and not result["is_error"]


def test_tool_error_is_returned_to_model():
    client = FakeClient([
        ([tool_use("t1", "read_file", path="/inexistant")], "tool_use"),
        ([text("ok")], "end_turn"),
    ])
    messages = [{"role": "user", "content": "lis"}]
    run(client, messages, TOOLS, default_handlers(lambda c: False))
    assert messages[2]["content"][0]["is_error"] is True


def test_bash_requires_approval():
    handlers = default_handlers(lambda c: False)
    assert handlers["run_bash"](command="echo hi") == "Refusé par l'utilisateur."
    assert default_handlers(lambda c: True)["run_bash"](command="echo hi").strip() == "hi"


def test_max_turns_guard():
    client = FakeClient([([tool_use(f"t{i}", "list_dir")], "tool_use") for i in range(3)])
    out = run(client, [{"role": "user", "content": "x"}], TOOLS, default_handlers(lambda c: False), max_turns=3)
    assert "maximal" in out


def test_pause_turn_resumes_without_tool_results():
    from types import SimpleNamespace as NS
    srv = NS(type="server_tool_use", id="s1", name="web_search", input={"query": "x"})
    client = FakeClient([([srv], "pause_turn"), ([text("réponse")], "end_turn")])
    messages = [{"role": "user", "content": "cherche"}]
    out = run(client, messages, TOOLS, default_handlers(lambda c: False))
    assert out == "réponse"
    # le tour en pause est renvoyé tel quel, sans message user intercalé
    assert [m["role"] for m in messages] == ["user", "assistant", "assistant"]
