"""Mémoire persistante : notes durables + sauvegarde/reprise de la conversation."""
import json
from pathlib import Path

STATE_DIR = Path(".agent")
NOTES = STATE_DIR / "memory.md"
SESSION = STATE_DIR / "session.json"

REMEMBER_TOOL = {
    "name": "remember",
    "description": (
        "Enregistre une information durable (préférence de l'utilisateur, fait sur le projet, décision) "
        "qui sera rappelée dans les prochaines sessions. Une note courte et autonome par appel."
    ),
    "input_schema": {"type": "object", "properties": {"note": {"type": "string"}}, "required": ["note"]},
}


def load_notes(path: Path = NOTES) -> str:
    return path.read_text().strip() if path.exists() else ""


def remember(note: str, path: Path = NOTES) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(f"- {note.strip()}\n")
    return "Noté."


def system_with_memory(base: str, path: Path = NOTES) -> str:
    notes = load_notes(path)
    if not notes:
        return base
    return f"{base}\n\n## Mémoire (notes des sessions précédentes)\n{notes}"


def _block_to_dict(block):
    if isinstance(block, dict):
        return block
    return block.model_dump(mode="json", exclude_none=True)


def save_session(messages: list, path: Path = SESSION) -> None:
    """Sérialise l'historique. Les blocs de l'assistant (réflexion incluse) sont conservés tels quels."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for m in messages:
        content = m["content"]
        if not isinstance(content, str):
            content = [_block_to_dict(b) for b in content]
        out.append({"role": m["role"], "content": content})
    path.write_text(json.dumps(out, ensure_ascii=False))


def load_session(path: Path = SESSION) -> list:
    return json.loads(path.read_text()) if path.exists() else []
