import json

from fastapi.testclient import TestClient

from agent.web import create_app
from tests.fakes import FakeClient, call, reply


def events(resp):
    return [json.loads(p[6:]) for p in resp.text.split("\n\n") if p.startswith("data: ")]


def test_chat_streams_text_and_tool_events():
    fake = FakeClient([reply(None, call("t1", "list_dir", path=".")), reply("voilà")])
    http = TestClient(create_app(fake))
    evs = events(http.post("/chat", json={"session_id": "s", "message": "liste"}))
    assert evs[0]["type"] == "tool" and evs[0]["name"] == "list_dir"
    assert "".join(e["text"] for e in evs if e["type"] == "text") == "voilà"


def test_history_kept_per_session_and_bash_refused():
    fake = FakeClient([
        reply(None, call("t1", "run_bash", command="echo hi")),
        reply("ok"),
        reply("encore"),
    ])
    http = TestClient(create_app(fake))
    http.post("/chat", json={"session_id": "s", "message": "bash"})
    tool_msg = next(m for m in fake.calls[1]["messages"] if m["role"] == "tool")
    assert tool_msg["content"] == "Refusé par l'utilisateur."
    http.post("/chat", json={"session_id": "s", "message": "suite"})
    assert len(fake.calls[2]["messages"]) >= 6  # system + historique de la session conservé


def test_index_page():
    assert "<title>Agent</title>" in TestClient(create_app(FakeClient([]))).get("/").text
