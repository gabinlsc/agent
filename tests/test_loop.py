from agent.loop import run
from agent.tools import TOOLS, default_handlers
from tests.fakes import FakeClient, call, reply

H = lambda: default_handlers(lambda c: False)  # noqa: E731


def test_loop_executes_tool_then_answers(tmp_path):
    target = tmp_path / "a.txt"
    client = FakeClient([
        reply(None, call("t1", "write_file", path=str(target), content="salut")),
        reply("fait"),
    ])
    messages = [{"role": "user", "content": "écris"}]
    out = run(client, messages, TOOLS, H())
    assert out == "fait"
    assert target.read_text() == "salut"  # arguments reconstitués depuis les morceaux du flux
    assert messages[2] == {"role": "tool", "tool_call_id": "t1", "content": f"{len('salut')} caractères écrits dans {target}"}


def test_system_prompt_is_sent_first_but_not_stored():
    client = FakeClient([reply("ok")])
    messages = [{"role": "user", "content": "x"}]
    run(client, messages, TOOLS, H(), system="SYS", model="deepseek-chat")
    assert client.calls[0]["messages"][0] == {"role": "system", "content": "SYS"}
    assert all(m["role"] != "system" for m in messages)


def test_tool_error_is_returned_to_model():
    client = FakeClient([reply(None, call("t1", "read_file", path="/inexistant")), reply("ok")])
    messages = [{"role": "user", "content": "lis"}]
    run(client, messages, TOOLS, H())
    assert messages[2]["content"].startswith("Erreur")


def test_unknown_tool_and_invalid_json():
    client = FakeClient([
        reply(None, call("t1", "inconnu"), ("t2", "list_dir", "{pas du json")),
        reply("ok"),
    ])
    messages = [{"role": "user", "content": "x"}]
    run(client, messages, TOOLS, H())
    assert "inconnu" in messages[2]["content"]
    assert "JSON" in messages[3]["content"]


def test_bash_requires_approval():
    assert default_handlers(lambda c: False)["run_bash"](command="echo hi") == "Refusé par l'utilisateur."
    assert default_handlers(lambda c: True)["run_bash"](command="echo hi").strip() == "hi"


def test_fetch_url_rejects_non_http():
    import pytest

    with pytest.raises(ValueError):
        default_handlers(lambda c: False)["fetch_url"](url="file:///etc/passwd")


def test_max_turns_guard():
    client = FakeClient([reply(None, call(f"t{i}", "list_dir")) for i in range(3)])
    out = run(client, [{"role": "user", "content": "x"}], TOOLS, H(), max_turns=3)
    assert "maximal" in out


def test_qwen3_thinking_disabled_by_default():
    from agent.config import system_for

    assert system_for("qwen3:8b", "SYS", thinking=False).endswith("/no_think")
    assert system_for("qwen3:8b", "SYS", thinking=True) == "SYS"
    assert system_for("deepseek-chat", "SYS", thinking=False) == "SYS"
    assert system_for("qwen2.5:7b", "SYS", thinking=False) == "SYS"
