"""Interface terminal."""
import argparse
import sys

import anthropic

from .loop import MODEL, SYSTEM, fmt_args, run
from .memory import REMEMBER_TOOL, load_notes, load_session, remember, save_session, system_with_memory
from .tools import TOOLS, default_handlers


def approve_in_terminal(command: str) -> bool:
    return input(f"\n  ⚠️  Exécuter `{command}` ? [o/N] ").strip().lower() == "o"


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent")
    parser.add_argument("--resume", action="store_true", help="reprendre la dernière conversation")
    args = parser.parse_args()

    client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY
    handlers = {**default_handlers(approve_in_terminal), "remember": remember}
    tools = [*TOOLS, REMEMBER_TOOL]
    system = system_with_memory(SYSTEM)
    messages: list = load_session() if args.resume else []
    print(f"Agent prêt ({MODEL}). 'exit' pour quitter, '/memoire' pour voir les notes.\n")
    while True:
        try:
            user = input("toi > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user in ("exit", "quit"):
            break
        if not user:
            continue
        if user == "/memoire":
            print(load_notes() or "(aucune note)")
            continue
        messages.append({"role": "user", "content": user})
        print("agent > ", end="")
        try:
            run(
                client, messages, tools, handlers, system=system,
                on_text=lambda t: print(t, end="", flush=True),
                on_tool=lambda n, a: print(f"\n  🔧 {n}({fmt_args(a)})"),
            )
            print()
            save_session(messages)
        except anthropic.APIError as e:
            print(f"\n[erreur API] {e}", file=sys.stderr)
            messages.pop()
