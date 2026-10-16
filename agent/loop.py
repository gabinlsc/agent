"""La boucle agentique : appeler Claude, exécuter les outils demandés, recommencer."""
import json
from typing import Callable

import anthropic

MODEL = "claude-opus-5-5"
SYSTEM = (
    "Tu es un agent de développement qui travaille dans le dossier courant. "
    "Utilise les outils pour explorer, lire, modifier des fichiers et lancer des commandes. "
    "Réponds en français, de façon concise."
)


def run_tool(handlers: dict[str, Callable[..., str]], name: str, args: dict) -> tuple[str, bool]:
    try:
        return str(handlers[name](**args)), False
    except Exception as e:  # renvoyée au modèle pour qu'il s'adapte
        return f"Erreur : {e}", True


def run(
    client: anthropic.Anthropic,
    messages: list,
    tools: list,
    handlers: dict[str, Callable[..., str]],
    system: str = SYSTEM,
    on_text: Callable[[str], None] = lambda t: None,
    on_tool: Callable[[str, dict], None] = lambda n, a: None,
    model: str = MODEL,
    max_turns: int = 30,
) -> str:
    """Boucle jusqu'à ce que Claude réponde sans demander d'outil. Renvoie le dernier texte."""
    for _ in range(max_turns):
        with client.messages.stream(
            model=model,
            max_tokens=16000,
            system=system,
            tools=tools,
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                on_text(text)
            response = stream.get_final_message()

        # Contenu renvoyé tel quel (blocs de réflexion inclus).
        messages.append({"role": "assistant", "content": response.content})

        # Les outils serveur (web_search) tournent chez Anthropic ; un tour long peut être mis en
        # pause : on renvoie simplement la conversation telle quelle pour qu'il reprenne.
        if response.stop_reason == "pause_turn":
            continue

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type == "tool_use":
                on_tool(block.name, block.input)
                out, is_error = run_tool(handlers, block.name, block.input)
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": out, "is_error": is_error}
                )
        # Tous les résultats dans UN seul message utilisateur.
        messages.append({"role": "user", "content": results})
    return "(arrêt : nombre maximal de tours atteint)"


def fmt_args(args: dict) -> str:
    return json.dumps(args, ensure_ascii=False)[:120]
