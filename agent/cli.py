"""Interface terminal."""
import sys

import anthropic

from .loop import MODEL, fmt_args, run
from .tools import TOOLS, default_handlers


def approve_in_terminal(command: str) -> bool:
    return input(f"\n  ⚠️  Exécuter `{command}` ? [o/N] ").strip().lower() == "o"


def main() -> None:
    client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY
    handlers = default_handlers(approve_in_terminal)
    messages: list = []
    print(f"Agent prêt ({MODEL}). 'exit' ou Ctrl+C pour quitter.\n")
    while True:
        try:
            user = input("toi > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user in ("exit", "quit"):
            break
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        print("agent > ", end="")
        try:
            run(
                client, messages, TOOLS, handlers,
                on_text=lambda t: print(t, end="", flush=True),
                on_tool=lambda n, a: print(f"\n  🔧 {n}({fmt_args(a)})"),
            )
            print()
        except anthropic.APIError as e:
            print(f"\n[erreur API] {e}", file=sys.stderr)
            messages.pop()
