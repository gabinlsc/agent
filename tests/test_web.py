import json

from fastapi.testclient import TestClient

from agent.web import create_app
from tests.fakes import FakeClient, text, tool_use


def events(resp):
    return [json.loads(p[6:]) for p in resp.text.split("\n\n") if p.startswith("data: ")]


def test_chat_streams_text_and_tool_events():
    fake = FakeClient([
        ([tool_use("t1", "list_dir", path=".")], "tool_use"),
        ([text("voilà")], "end_turn"),
    ])
    http = TestClient(create_app(fake))
    r = http.post("/chat", json={"session_id": "s", "message": "liste"})
    evs = events(r)
    assert [e["type"] for e in evs] == ["tool", "text"]
    assert evs[1]["text"] == "voilà"


def test_history_kept_per_session_and_bash_refused():
    fake = FakeClient([
        ([tool_use("t1", "run_bash", command="echo hi")], "tool_use"),
        ([text("ok")], "end_turn"),
        ([text("encore")], "end_turn"),
    ])
    http = TestClient(create_app(fake))
    http.post("/chat", json={"session_id": "s", "message": "bash"})
    results = fake.calls[1]["messages"][2]["content"][0]["content"]
    assert results == "Refusé par l'utilisateur."
    http.post("/chat", json={"session_id": "s", "message": "suite"})
    assert len(fake.calls[2]["messages"]) >= 5  # l'historique de la session est conservé


def test_index_page():
    assert "<title>Agent</title>" in TestClient(create_app(FakeClient([]))).get("/").text
