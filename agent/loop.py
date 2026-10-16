"""La boucle agentique : appeler le modèle, exécuter les outils demandés, recommencer."""
import json
from typing import Callable

from .config import MODEL

SYSTEM = (
    "Tu es un agent de développement qui travaille dans le dossier courant. "
    "Utilise les outils pour explorer, lire, modifier des fichiers et lancer des commandes. "
    "Réponds en français, de façon concise."
)


def run_tool(handlers: dict[str, Callable[..., str]], name: str, args: dict) -> str:
    if name not in handlers:
        return f"Erreur : outil inconnu « {name} »."
    try:
        return str(handlers[name](**args))
    except Exception as e:  # renvoyée au modèle pour qu'il s'adapte
        return f"Erreur : {e}"


def _stream_reply(client, model: str, system: str, messages: list, tools: list, on_text) -> dict:
    """Un appel en streaming ; reconstitue le message assistant (texte + appels d'outils)."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, *messages],
        tools=tools,
        temperature=0.3,
        stream=True,
    )
    parts: list[str] = []
    calls: dict[int, dict] = {}
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            parts.append(delta.content)
            on_text(delta.content)
        for tc in delta.tool_calls or []:  # les appels arrivent en morceaux, indexés
            c = calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
            c["id"] = tc.id or c["id"]
            if tc.function:
                c["name"] += tc.function.name or ""
                c["args"] += tc.function.arguments or ""
    text = "".join(parts)
    msg: dict = {"role": "assistant", "content": text or None}
    if calls:
        msg["tool_calls"] = [
            {
                "id": c["id"] or f"call_{i}",
                "type": "function",
                "function": {"name": c["name"], "arguments": c["args"] or "{}"},
            }
            for i, c in sorted(calls.items())
        ]
    return msg


def run(
    client,
    messages: list,
    tools: list,
    handlers: dict[str, Callable[..., str]],
    system: str = SYSTEM,
    on_text: Callable[[str], None] = lambda t: None,
    on_tool: Callable[[str, dict], None] = lambda n, a: None,
    model: str = MODEL,
    max_turns: int = 30,
) -> str:
    """Boucle jusqu'à ce que le modèle réponde sans demander d'outil. Renvoie le dernier texte."""
    for _ in range(max_turns):
        reply = _stream_reply(client, model, system, messages, tools, on_text)
        messages.append(reply)
        if "tool_calls" not in reply:
            return reply["content"] or ""
        for tc in reply["tool_calls"]:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
                if not isinstance(args, dict):
                    raise ValueError
            except ValueError:
                out = "Erreur : les arguments de l'outil ne sont pas un objet JSON valide."
                on_tool(name, {})
            else:
                on_tool(name, args)
                out = run_tool(handlers, name, args)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": out})
    return "(arrêt : nombre maximal de tours atteint)"


def fmt_args(args: dict) -> str:
    return json.dumps(args, ensure_ascii=False)[:120]
