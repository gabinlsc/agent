"""Windows ouvre les fichiers en cp1252 par défaut : tout accès fichier doit préciser l'encodage."""
import ast
from pathlib import Path

from agent.memory import load_session, save_session

ROOT = Path(__file__).resolve().parent.parent
TEXT_IO = {"read_text", "write_text", "open"}


def test_emoji_roundtrip(tmp_path):
    path = tmp_path / "s.json"
    msgs = [{"role": "assistant", "content": "Bonjour ! 😊 é à"}]
    save_session(msgs, path)
    assert load_session(path) == msgs
    assert "😊" in path.read_bytes().decode("utf-8")


def test_every_file_access_sets_encoding():
    missing = []
    for src in [*ROOT.glob("agent/*.py"), *ROOT.glob("evals/*.py")]:
        for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in TEXT_IO
                and not any(k.arg == "encoding" for k in node.keywords)
            ):
                missing.append(f"{src.name}:{node.lineno} .{node.func.attr}()")
    assert not missing, missing
