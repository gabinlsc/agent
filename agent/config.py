"""Configuration du modèle : tout serveur compatible OpenAI convient (Ollama, DeepSeek, OpenRouter…)."""
import os

BASE_URL = os.environ.get("AGENT_BASE_URL", "http://localhost:11434/v1")  # Ollama par défaut
MODEL = os.environ.get("AGENT_MODEL", "qwen3:8b")
API_KEY = os.environ.get("AGENT_API_KEY", "ollama")  # Ollama ignore la clé mais le SDK en exige une


def make_client():
    from openai import OpenAI

    return OpenAI(base_url=BASE_URL, api_key=API_KEY)
