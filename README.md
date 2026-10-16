# agent

Un agent LLM écrit à la main : une boucle autour d'un modèle + des outils locaux.
Il parle le protocole « OpenAI-compatible », donc il marche avec **Qwen/DeepSeek en local (gratuit, via Ollama)**
comme avec n'importe quelle API (DeepSeek, OpenRouter, …).

## Installation (gratuit, en local)

1. Installer [Ollama](https://ollama.com/download) (Windows : `winget install Ollama.Ollama`).
2. Télécharger un modèle qui gère les outils :
   ```bash
   ollama pull qwen3:8b       # ~5 Go ; qwen3:4b si peu de RAM, qwen3:14b ou qwen3-coder si GPU costaud
   ```
3. Installer et lancer l'agent :
   ```bash
   pip install -r requirements.txt
   python -m agent            # nouvelle conversation
   python -m agent --resume   # reprendre la dernière
   ```

## Changer de modèle / de fournisseur

Trois variables d'environnement (valeurs par défaut : Ollama + `qwen3:8b`) :

| Variable | Rôle | Défaut |
|---|---|---|
| `AGENT_BASE_URL` | adresse du serveur | `http://localhost:11434/v1` |
| `AGENT_MODEL` | nom du modèle | `qwen3:8b` |
| `AGENT_API_KEY` | clé API (ignorée par Ollama) | `ollama` |

Exemples (PowerShell : `$env:NOM = "valeur"`, bash : `export NOM=valeur`) :

```bash
# DeepSeek hébergé (payant mais très peu cher)
AGENT_BASE_URL=https://api.deepseek.com AGENT_MODEL=deepseek-chat AGENT_API_KEY=sk-... python -m agent
# OpenRouter
AGENT_BASE_URL=https://openrouter.ai/api/v1 AGENT_MODEL=qwen/qwen3-coder AGENT_API_KEY=sk-or-... python -m agent
```

`AGENT_THINKING=1` réactive le mode réflexion de Qwen3 (plus malin, mais bien plus lent ; désactivé par défaut).

## Si c'est lent

1. `ollama ps` : la colonne PROCESSOR doit afficher du GPU ; « 100% CPU » = lent par nature.
2. Prends un modèle plus petit : `ollama pull qwen3:4b` puis `AGENT_MODEL=qwen3:4b`.
3. Ou un modèle sans mode réflexion : `qwen2.5:7b` / `qwen2.5-coder:7b`.
4. Ou une API hébergée (DeepSeek : quelques centimes, quasi instantané).

Plus le modèle est gros, plus il utilise bien les outils : un petit modèle local se trompe plus souvent.

## Interface web

```bash
python -m agent.web   # http://127.0.0.1:8000
```

Chat en streaming dans le navigateur. `run_bash` y est désactivé (pas d'approbation possible).

## Évaluations

```bash
python -m evals                 # tous les cas, 1 passage chacun
python -m evals --runs 3 -k bug # répéter un cas (le LLM est non déterministe)
python -m evals --model qwen3:14b
```

Chaque cas tourne dans un dossier temporaire, avec une vérification automatique (fichier créé, bug corrigé,
réponse correcte…). Le bash y est toujours refusé. Utile pour comparer deux modèles ou deux prompts.

## Mémoire

- L'outil `remember` ajoute des notes durables dans `.agent/memory.md`, relues au démarrage suivant (`/memoire` pour les afficher).
- La conversation est sauvegardée dans `.agent/session.json` après chaque tour.

## Outils

`list_dir`, `read_file`, `write_file`, `run_bash` (avec approbation), `fetch_url` (page web),
`remember`, `delegate` (sous-agent en lecture seule au contexte vierge).

## Structure

- `agent/loop.py` : la boucle agentique (appel → outils → résultats → rappel)
- `agent/config.py` : modèle, adresse, clé
- `agent/tools.py` : outils locaux
- `agent/memory.py` : notes durables + sauvegarde/reprise de session
- `agent/subagent.py` : outil `delegate`
- `agent/web.py` : interface web (FastAPI, SSE)
- `agent/cli.py` : interface terminal
- `evals/` : cas d'évaluation et runner
- `tests/` : tests unitaires avec un faux client (aucun appel réseau) — `pytest`
