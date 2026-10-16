# agent

Un agent LLM écrit à la main : une boucle autour de l'API Claude + des outils locaux.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m agent            # nouvelle conversation
python -m agent --resume   # reprendre la dernière
```

## Interface web

```bash
python -m agent.web   # http://127.0.0.1:8000
```

Chat en streaming dans le navigateur. `run_bash` y est désactivé (pas d'approbation possible).

## Mémoire

- L'outil `remember` ajoute des notes durables dans `.agent/memory.md`, relues au démarrage suivant (`/memoire` pour les afficher).
- La conversation est sauvegardée dans `.agent/session.json` après chaque tour.

## Structure

- `agent/loop.py` : la boucle agentique (appel → outils → résultats → rappel)
- `agent/tools.py` : outils locaux (`list_dir`, `read_file`, `write_file`, `run_bash` avec approbation)
- `agent/memory.py` : notes durables + sauvegarde/reprise de session
- `agent/websearch.py` : recherche web (outil serveur `web_search`, pause_turn géré par la boucle)
- `agent/subagent.py` : outil `delegate` — un sous-agent en lecture seule, au contexte vierge, qui rend un compte rendu
- `agent/web.py` : interface web (FastAPI, SSE)
- `agent/cli.py` : interface terminal
- `tests/` : tests unitaires avec un faux client (aucun appel réseau) — `pytest`
