from agent.memory import load_notes, load_session, remember, save_session, system_with_memory


def test_notes_roundtrip_and_system_prompt(tmp_path):
    notes = tmp_path / "m.md"
    assert system_with_memory("base", notes) == "base"
    remember("L'utilisateur préfère le français", notes)
    assert "préfère le français" in load_notes(notes)
    assert "Mémoire" in system_with_memory("base", notes)


def test_session_roundtrip(tmp_path):
    path = tmp_path / "s.json"
    messages = [
        {"role": "user", "content": "salut"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "t1", "type": "function", "function": {"name": "list_dir", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "a"},
    ]
    save_session(messages, path)
    assert load_session(path) == messages


def test_load_missing_session(tmp_path):
    assert load_session(tmp_path / "nope.json") == []
