"""Interface terminal."""
import argparse
import sys

import openai

from .config import BASE_URL, MODEL, make_client
from .loop import SYSTEM, fmt_args, run
from .memory import REMEMBER_TOOL, load_notes, load_session, remember, save_session, system_with_memory
from .subagent import DELEGATE_TOOL, make_delegate
from .tools import TOOLS, default_handlers


def approve_in_terminal(command: str) -> bool:
    return input(f"\n  ⚠️  Exécuter `{command}` ? [o/N] ").strip().lower() == "o"


def main() -> None:
    for stream in (sys.stdout, sys.stderr):  # consoles Windows en cp1252 : ne jamais planter sur un emoji
        stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="agent")
    parser.add_argument("--resume", action="store_true", help="reprendre la dernière conversation")
    args = parser.parse_args()

    client = make_client()
    show_tool = lambda n, a: print(f"\n  🔧 {n}({fmt_args(a)})")  # noqa: E731
    handlers = {
        **default_handlers(approve_in_terminal),
        "remember": remember,
        "delegate": make_delegate(client, show_tool),
    }
    tools = [*TOOLS, REMEMBER_TOOL, DELEGATE_TOOL]
    system = system_with_memory(SYSTEM)
    messages: list = load_session() if args.resume else []
    print(f"Agent prêt ({MODEL} via {BASE_URL}). 'exit' pour quitter, '/memoire' pour voir les notes.\n")
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
        start = len(messages)
        messages.append({"role": "user", "content": user})
        print("agent > ", end="")
        try:
            run(
                client, messages, tools, handlers, system=system,
                on_text=lambda t: print(t, end="", flush=True),
                on_tool=show_tool,
            )
            print()
            save_session(messages)
        except openai.APIConnectionError:
            print(f"\n[erreur] Impossible de joindre {BASE_URL}. Ollama est-il lancé ?", file=sys.stderr)
            del messages[start:]
        except openai.OpenAIError as e:
            print(f"\n[erreur API] {e}", file=sys.stderr)
            del messages[start:]
