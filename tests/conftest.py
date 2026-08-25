"""Impalcatura dei test.

Due regole che valgono per tutti i file qui dentro.

**Niente scritture nel repository.** Gli strumenti che scrivono - apply.py,
covers.py, merge.py - si provano puntandoli a una cartella temporanea, mai al
dizionario o al mod veri. Un test che sporca l'albero di lavoro e' un test che
la prossima volta nessuno lancia.

**Il gioco non e' un requisito.** Chi clona il repository puo' non averlo
installato: i test che ne hanno bisogno si marcano `needs_game` e si saltano da
soli, invece di fallire e far credere che il codice sia rotto.
"""
import importlib
import os
import subprocess
import sys

import pytest

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(PROJ, "tools")
sys.path.insert(0, TOOLS)


def tool(name):
    """Il modulo di uno strumento, importato una volta sola."""
    return importlib.import_module(name)


def run_script(name, *args, timeout=300):
    """Lo strumento lanciato come lo lancia una persona, in un processo a parte.

    Serve per i dieci script che fanno il loro lavoro al livello del modulo:
    importarli vorrebbe dire eseguirli.
    """
    return subprocess.run([sys.executable, os.path.join(TOOLS, name + ".py"), *args],
                          capture_output=True, text=True, cwd=PROJ, timeout=timeout)


@pytest.fixture(scope="session")
def game_installed():
    b = tool("bohloc")
    return os.path.isdir(b.CORE)


@pytest.fixture
def needs_game(game_installed):
    if not game_installed:
        pytest.skip("il gioco non e' installato: percorsi.json, chiave «game»")


@pytest.fixture
def dictionary(tmp_path):
    """Un dizionario minimo nella forma vera: overrides + strings."""
    import json
    p = tmp_path / "it.json"
    p.write_text(json.dumps({
        "overrides": {},
        "strings": {"The Iron Book": "Il Libro di Ferro",
                    "Post Office Counter": "Bancone dell'Ufficio Postale"},
    }, ensure_ascii=False), encoding="utf-8")
    return p
