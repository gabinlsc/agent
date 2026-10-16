from agent.loop import run
from agent.subagent import DELEGATE_TOOL, READ_ONLY, make_delegate
from agent.tools import TOOLS, default_handlers, tool_name
from tests.fakes import FakeClient, call, reply


def test_delegate_runs_isolated_conversation():
    client = FakeClient([
        reply(None, call("d1", "delegate", task="cherche X")),  # agent principal
        reply("X vaut 42"),                                      # sous-agent
        reply("la réponse est 42"),                              # agent principal
    ])
    handlers = {**default_handlers(lambda c: False), "delegate": make_delegate(client)}
    messages = [{"role": "user", "content": "combien vaut X ?"}]
    out = run(client, messages, [*TOOLS, DELEGATE_TOOL], handlers)
    assert out == "la réponse est 42"
    sub_msgs = client.calls[1]["messages"]
    assert [m["role"] for m in sub_msgs] == ["system", "user"]  # contexte vierge
    assert sub_msgs[1]["content"] == "cherche X"
    assert messages[2]["content"] == "X vaut 42"  # seul le compte rendu remonte


def test_subagent_is_read_only_and_cannot_recurse():
    assert {tool_name(t) for t in READ_ONLY} == {"list_dir", "read_file", "fetch_url"}
