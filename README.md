# agent

Un agent LLM écrit à la main : une boucle autour de l'API Claude + des outils locaux.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python -m agent
```

## Structure

- `agent/loop.py` : la boucle agentique (appel → outils → résultats → rappel)
- `agent/tools.py` : outils locaux (`list_dir`, `read_file`, `write_file`, `run_bash` avec approbation)
- `agent/cli.py` : interface terminal
- `tests/` : tests unitaires avec un faux client (aucun appel réseau) — `pytest`
