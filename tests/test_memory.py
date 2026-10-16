from anthropic.types import TextBlock, ToolUseBlock

from agent.memory import load_notes, load_session, remember, save_session, system_with_memory


def test_notes_roundtrip_and_system_prompt(tmp_path):
    notes = tmp_path / "m.md"
    assert system_with_memory("base", notes) == "base"
    remember("L'utilisateur préfère le français", notes)
    assert "préfère le français" in load_notes(notes)
    assert "Mémoire" in system_with_memory("base", notes)


def test_session_roundtrip_with_sdk_blocks(tmp_path):
    path = tmp_path / "s.json"
    messages = [
        {"role": "user", "content": "salut"},
        {"role": "assistant", "content": [
            TextBlock(type="text", text="je regarde", citations=None),
            ToolUseBlock(type="tool_use", id="t1", name="list_dir", input={"path": "."}),
        ]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "a"}]},
    ]
    save_session(messages, path)
    loaded = load_session(path)
    assert loaded[0] == messages[0]
    assert loaded[1]["content"][1] == {"type": "tool_use", "id": "t1", "name": "list_dir", "input": {"path": "."}}
    assert loaded[2] == messages[2]


def test_load_missing_session(tmp_path):
    assert load_session(tmp_path / "nope.json") == []
