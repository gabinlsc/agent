from agent.loop import run
from agent.subagent import DELEGATE_TOOL, READ_ONLY, make_delegate
from agent.tools import TOOLS, default_handlers
from tests.fakes import FakeClient, text, tool_use


def test_delegate_runs_isolated_conversation():
    client = FakeClient([
        ([tool_use("d1", "delegate", task="cherche X")], "tool_use"),  # agent principal
        ([text("X vaut 42")], "end_turn"),                              # sous-agent
        ([text("la réponse est 42")], "end_turn"),                      # agent principal
    ])
    handlers = {**default_handlers(lambda c: False), "delegate": make_delegate(client)}
    messages = [{"role": "user", "content": "combien vaut X ?"}]
    out = run(client, messages, [*TOOLS, DELEGATE_TOOL], handlers)
    assert out == "la réponse est 42"
    sub_call = client.calls[1]
    assert sub_call["messages"][0]["content"] == "cherche X"  # contexte vierge
    assert messages[2]["content"][0]["content"] == "X vaut 42"  # seul le compte rendu remonte


def test_subagent_is_read_only_and_cannot_recurse():
    names = {t["name"] for t in READ_ONLY}
    assert names == {"list_dir", "read_file", "web_search"}
