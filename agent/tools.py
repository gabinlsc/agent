"""Outils locaux : une définition (format OpenAI) + une fonction Python chacun."""
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable


def make_tool(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)},
        },
    }


def tool_name(tool: dict) -> str:
    return tool["function"]["name"]


TOOLS = [
    make_tool("list_dir", "Liste le contenu d'un dossier.", {"path": {"type": "string", "description": "Dossier, '.' par défaut"}}),
    make_tool("read_file", "Lit un fichier texte et renvoie son contenu.", {"path": {"type": "string"}}, ("path",)),
    make_tool(
        "write_file",
        "Crée ou écrase un fichier avec le contenu donné.",
        {"path": {"type": "string"}, "content": {"type": "string"}},
        ("path", "content"),
    ),
    make_tool(
        "run_bash",
        "Exécute une commande shell (l'utilisateur doit l'approuver).",
        {"command": {"type": "string"}},
        ("command",),
    ),
    make_tool(
        "fetch_url",
        "Télécharge une page web (http/https) et renvoie son texte brut.",
        {"url": {"type": "string"}},
        ("url",),
    ),
]


def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(p.name + ("/" if p.is_dir() else "") for p in Path(path).iterdir()))


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")[:50_000]


def write_file(path: str, content: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"{len(content)} caractères écrits dans {path}"


def fetch_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("seules les URL http(s) sont acceptées")
    req = urllib.request.Request(url, headers={"User-Agent": "agent/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read(500_000).decode("utf-8", errors="replace")
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()[:20_000]


def make_run_bash(approve: Callable[[str], bool]) -> Callable[[str], str]:
    """`approve` décide si une commande peut s'exécuter (CLI : prompt, web : refus)."""

    def run_bash(command: str) -> str:
        if not approve(command):
            return "Refusé par l'utilisateur."
        r = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        return (r.stdout + r.stderr)[-10_000:] or f"(code retour {r.returncode})"

    return run_bash


def default_handlers(approve: Callable[[str], bool]) -> dict[str, Callable[..., str]]:
    return {
        "list_dir": list_dir,
        "read_file": read_file,
        "write_file": write_file,
        "fetch_url": fetch_url,
        "run_bash": make_run_bash(approve),
    }
