"""Cas d'évaluation : une tâche, un décor de départ, et une vérification automatique."""
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Case:
    name: str
    prompt: str
    check: Callable[[Path, str], bool]  # (dossier de travail, réponse finale) -> réussi ?
    setup: Callable[[Path], None] = lambda d: None


def _setup_config(d: Path) -> None:
    (d / "config.json").write_text('{"name": "demo", "server": {"port": 8421}}')


def _setup_pyfiles(d: Path) -> None:
    for n in ("a.py", "b.py", "c.py"):
        (d / n).write_text("pass\n")
    (d / "notes.txt").write_text("x\n")


def _setup_bug(d: Path) -> None:
    (d / "calc.py").write_text("def add(a, b):\n    return a - b\n")


def _fixed(d: Path, answer: str) -> bool:
    ns: dict = {}
    exec((d / "calc.py").read_text(), ns)
    return ns["add"](2, 3) == 5


CASES = [
    Case(
        "write_file",
        "Crée un fichier hello.txt contenant exactement : bonjour",
        lambda d, a: (d / "hello.txt").exists() and (d / "hello.txt").read_text().strip() == "bonjour",
    ),
    Case(
        "read_config",
        "Quel port est configuré dans config.json ? Réponds avec le nombre.",
        lambda d, a: "8421" in a,
        _setup_config,
    ),
    Case(
        "count_files",
        "Combien de fichiers .py y a-t-il dans le dossier courant ? Réponds avec le nombre.",
        lambda d, a: "3" in a,
        _setup_pyfiles,
    ),
    Case("fix_bug", "La fonction add de calc.py est fausse. Corrige-la.", _fixed, _setup_bug),
    Case(
        "remember",
        "Retiens que je m'appelle Gabin et que je préfère les réponses courtes.",
        lambda d, a: "gabin" in (d / ".agent" / "memory.md").read_text().lower()
        if (d / ".agent" / "memory.md").exists()
        else False,
    ),
]
