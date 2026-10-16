# agent

Un agent LLM écrit à la main : une boucle autour de l'API Claude + des outils locaux.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m agent            # nouvelle conversation
python -m agent --resume   # reprendre la dernière
```

## Mémoire

- L'outil `remember` ajoute des notes durables dans `.agent/memory.md`, relues au démarrage suivant (`/memoire` pour les afficher).
- La conversation est sauvegardée dans `.agent/session.json` après chaque tour.

## Structure

- `agent/loop.py` : la boucle agentique (appel → outils → résultats → rappel)
- `agent/tools.py` : outils locaux (`list_dir`, `read_file`, `write_file`, `run_bash` avec approbation)
- `agent/memory.py` : notes durables + sauvegarde/reprise de session
- `agent/cli.py` : interface terminal
- `tests/` : tests unitaires avec un faux client (aucun appel réseau) — `pytest`
