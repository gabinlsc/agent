"""Exécute les cas d'évaluation dans des dossiers temporaires et mesure le taux de réussite."""
import argparse
import os
import tempfile
import time
from pathlib import Path

from agent.config import MODEL, make_client
from agent.loop import SYSTEM, run
from agent.memory import REMEMBER_TOOL, remember, system_with_memory
from agent.tools import TOOLS, default_handlers

from .cases import CASES, Case


def run_case(client, case: Case, model: str = MODEL) -> dict:
    """Joue un cas dans un dossier jetable. Le bash est toujours refusé (évaluation sûre)."""
    previous = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        case.setup(workdir)
        os.chdir(workdir)  # les outils travaillent en chemins relatifs
        start = time.time()
        try:
            messages = [{"role": "user", "content": case.prompt}]
            handlers = {**default_handlers(lambda c: False), "remember": remember}
            answer = run(
                client, messages, [*TOOLS, REMEMBER_TOOL], handlers,
                system=system_with_memory(SYSTEM), model=model, max_turns=15,
            )
            passed = bool(case.check(workdir, answer))
            error = None
        except Exception as e:  # une erreur d'API ou de vérification = cas échoué, pas un crash
            passed, error = False, f"{type(e).__name__}: {e}"
        finally:
            os.chdir(previous)
        return {"name": case.name, "passed": passed, "seconds": round(time.time() - start, 1), "error": error}


def main() -> None:
    parser = argparse.ArgumentParser(prog="evals")
    parser.add_argument("-k", help="ne lancer que les cas dont le nom contient ce texte")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--runs", type=int, default=1, help="répétitions par cas (le LLM est non déterministe)")
    args = parser.parse_args()

    client = make_client()
    cases = [c for c in CASES if not args.k or args.k in c.name]
    total = passed = 0
    for case in cases:
        results = [run_case(client, case, args.model) for _ in range(args.runs)]
        ok = sum(r["passed"] for r in results)
        total += len(results)
        passed += ok
        errs = [r["error"] for r in results if r["error"]]
        print(f"{'✅' if ok == len(results) else '❌'} {case.name:<14} {ok}/{len(results)}  "
              f"{sum(r['seconds'] for r in results):.0f}s" + (f"  {errs[0]}" if errs else ""))
    print(f"\nScore : {passed}/{total} ({100 * passed / max(total, 1):.0f}%) — modèle {args.model}")


if __name__ == "__main__":
    main()
