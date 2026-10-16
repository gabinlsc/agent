"""Outils locaux : une définition (schéma JSON) + une fonction Python chacun."""
import subprocess
from pathlib import Path
from typing import Callable

TOOLS = [
    {
        "name": "list_dir",
        "description": "Liste le contenu d'un dossier.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Dossier, '.' par défaut"}},
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Lit un fichier texte et renvoie son contenu.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "write_file",
        "description": "Crée ou écrase un fichier avec le contenu donné.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_bash",
        "description": "Exécute une commande shell (l'utilisateur doit l'approuver).",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    },
]


def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in Path(path).iterdir()))


def read_file(path: str) -> str:
    return Path(path).read_text()[:50_000]


def write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"{len(content)} caractères écrits dans {path}"


def make_run_bash(approve: Callable[[str], bool]) -> Callable[[str], str]:
    """`approve` décide si une commande peut s'exécuter (CLI : prompt, web : refus)."""

    def run_bash(command: str) -> str:
        if not approve(command):
            return "Refusé par l'utilisateur."
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return (r.stdout + r.stderr)[-10_000:] or f"(code retour {r.returncode})"

    return run_bash


def default_handlers(approve: Callable[[str], bool]) -> dict[str, Callable[..., str]]:
    return {
        "list_dir": list_dir,
        "read_file": read_file,
        "write_file": write_file,
        "run_bash": make_run_bash(approve),
    }
