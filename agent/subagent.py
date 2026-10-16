"""Sous-agents : l'agent principal délègue une tâche à une instance au contexte vierge."""
from typing import Callable

import anthropic

from .loop import run
from .tools import TOOLS, list_dir, read_file
from .websearch import WEB_SEARCH_TOOL

SUBAGENT_SYSTEM = (
    "Tu es un sous-agent de recherche. Tu reçois une tâche précise, tu l'accomplis avec tes outils "
    "en lecture seule, puis tu rends un compte rendu court et factuel (le contexte de ta recherche "
    "est jeté : ne renvoie que ce dont l'agent principal a besoin)."
)

DELEGATE_TOOL = {
    "name": "delegate",
    "description": (
        "Confie une tâche de recherche/lecture à un sous-agent au contexte vierge (lecture seule + web). "
        "Utile pour explorer beaucoup de fichiers ou de pages sans encombrer ta propre conversation. "
        "La tâche doit être autonome : le sous-agent ne voit pas ta conversation."
    ),
    "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]},
}

# Pas de write_file / run_bash / delegate : un sous-agent ne modifie rien et ne se multiplie pas.
READ_ONLY = [t for t in TOOLS if t["name"] in ("list_dir", "read_file")] + [WEB_SEARCH_TOOL]
READ_ONLY_HANDLERS = {"list_dir": list_dir, "read_file": read_file}


def make_delegate(
    client: anthropic.Anthropic, on_tool: Callable[[str, dict], None] = lambda n, a: None
) -> Callable[[str], str]:
    def delegate(task: str) -> str:
        messages = [{"role": "user", "content": task}]
        return run(
            client, messages, READ_ONLY, READ_ONLY_HANDLERS,
            system=SUBAGENT_SYSTEM, on_tool=lambda n, a: on_tool(f"  ↳ {n}", a), max_turns=15,
        )

    return delegate
