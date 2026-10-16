"""Configuration du modèle : tout serveur compatible OpenAI convient (Ollama, DeepSeek, OpenRouter…)."""
import os

BASE_URL = os.environ.get("AGENT_BASE_URL", "http://localhost:11434/v1")  # Ollama par défaut
MODEL = os.environ.get("AGENT_MODEL", "qwen3:8b")
API_KEY = os.environ.get("AGENT_API_KEY", "ollama")  # Ollama ignore la clé mais le SDK en exige une

# Qwen3 « réfléchit » longuement avant de répondre (très lent sur CPU). Désactivé par défaut ;
# AGENT_THINKING=1 le réactive pour les tâches difficiles.
THINKING = os.environ.get("AGENT_THINKING", "0") == "1"


def system_for(model: str, system: str, thinking: bool = THINKING) -> str:
    """Qwen3 comprend l'interrupteur « /no_think » placé dans le prompt système."""
    if model.lower().startswith("qwen3") and not thinking:
        return f"{system}\n/no_think"
    return system


def make_client():
    from openai import OpenAI

    return OpenAI(base_url=BASE_URL, api_key=API_KEY)
