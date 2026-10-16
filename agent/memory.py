"""Mémoire persistante : notes durables + sauvegarde/reprise de la conversation."""
import json
from pathlib import Path

from .tools import make_tool

STATE_DIR = Path(".agent")
NOTES = STATE_DIR / "memory.md"
SESSION = STATE_DIR / "session.json"

REMEMBER_TOOL = make_tool(
    "remember",
    "Enregistre une information durable (préférence de l'utilisateur, fait sur le projet, décision) "
    "qui sera rappelée dans les prochaines sessions. Une note courte et autonome par appel.",
    {"note": {"type": "string"}},
    ("note",),
)


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


def save_session(messages: list, path: Path = SESSION) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(messages, ensure_ascii=False))


def load_session(path: Path = SESSION) -> list:
    return json.loads(path.read_text()) if path.exists() else []
