"""Ogni script del progetto, preso una volta sola.

Non e' un test di logica: e' la rete che prende gli errori grossolani - un file
che non compila piu' dopo un rinomino, una riga d'uso che documenta un flag che
non esiste, un modulo che parte da solo appena lo importi. Sono esattamente i
guasti che un refactor introduce e che nessun test mirato vedrebbe, perche' i
test mirati importano solo cio' che gia' sanno che funziona.
"""
import ast
import glob
import os
import re

import pytest

from conftest import PROJ, TOOLS, run_script, tool

SCRIPT = sorted(os.path.basename(p)[:-3] for p in glob.glob(os.path.join(TOOLS, "*.py")))

# I dieci che fanno il loro lavoro al livello del modulo: importarli vuol dire
# eseguirli, quindi si provano da fuori, in un processo a parte.
RUN_ON_IMPORT = {"coverage", "donottranslate", "glyphcheck", "integrity",
                       "refine", "sample", "style", "style2", "style3", "uicheck"}

# ...tranne quello che, girando, riscrive un file del repository. Lanciarlo in
# un test vuol dire lasciare l'albero di lavoro sporco, e infatti la prima
# versione di questo file aggiungeva una riga a docs/glossario-non-tradurre.json
# a ogni esecuzione della suite.
WRITE_TO_REPO = {"donottranslate"}


def test_every_script_is_present():
    assert len(SCRIPT) >= 39, "qualche strumento e' sparito dalla cartella tools/"


@pytest.mark.parametrize("name", SCRIPT)
def test_parses(name):
    ast.parse(open(os.path.join(TOOLS, name + ".py"), encoding="utf-8").read())


@pytest.mark.parametrize("name", SCRIPT)
def test_has_a_docstring(name):
    tree = ast.parse(open(os.path.join(TOOLS, name + ".py"), encoding="utf-8").read())
    doc = ast.get_docstring(tree)
    assert doc and len(doc.strip()) > 20, f"{name}.py non dice a che cosa serve"


@pytest.mark.parametrize("name", [n for n in SCRIPT if n not in RUN_ON_IMPORT])
def test_imports_without_doing_anything(name):
    """Importare uno strumento non deve leggere il dizionario ne' scrivere."""
    tool(name)


def italian_identifiers(source):
    italian = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            italian |= {node.name} & ITALIAN_WORDS
            italian |= {a.arg for a in node.args.args} & ITALIAN_WORDS
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            italian |= {node.id} & ITALIAN_WORDS
    return italian


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(PROJ, "tests", "*.py"))))
def test_no_italian_identifiers_in_the_tests_either(path):
    """La stessa regola vale qui: i nomi in inglese, la prosa in italiano.

    Senza questo controllo la regola varrebbe per tools/ e non per tests/, ed e'
    esattamente il posto dove si scrive di fretta.
    """
    italian = italian_identifiers(open(path, encoding="utf-8").read())
    assert not italian, f"{os.path.basename(path)} ha identificatori italiani: {sorted(italian)}"


@pytest.mark.parametrize("name", SCRIPT)
def test_no_italian_identifiers(name):
    """I nomi in inglese: la prosa nei commenti e nei docstring resta italiana."""
    source = open(os.path.join(TOOLS, name + ".py"), encoding="utf-8").read()
    italian = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            italian |= {node.name} & ITALIAN_WORDS
            italian |= {a.arg for a in node.args.args} & ITALIAN_WORDS
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            italian |= {node.id} & ITALIAN_WORDS
    assert not italian, f"{name}.py ha ancora identificatori italiani: {sorted(italian)}"


# un campione: le parole che il refactor ha tradotto e che non devono tornare
ITALIAN_WORDS = {
    "fetta", "fette", "lastra", "lastre", "sigla", "dorsi", "riga", "righe", "parola",
    "parole", "campo", "campi", "voce", "voci", "resa", "rese", "chiave", "elenco",
    "scrivi", "leggi", "carica", "stampa", "conta", "prova", "verifica", "esegui",
    "percorso", "cartella", "nome", "nomi", "testo", "testi", "titolo", "titoli",
}


@pytest.mark.parametrize("name", sorted(RUN_ON_IMPORT - WRITE_TO_REPO))
@pytest.mark.needs_game
@pytest.mark.slow
def test_scripts_that_read_the_game_run(name, needs_game):
    r = run_script(name)
    assert r.returncode in (0, 1), f"{name}.py e' morto: {r.stderr[-400:]}"
    assert r.stdout.strip(), f"{name}.py non ha detto niente"


@pytest.mark.parametrize("name", sorted(WRITE_TO_REPO))
def test_scripts_that_write_are_never_executed(name):
    """Compilano e si leggono, ma non si lanciano: riscriverebbero il repository."""
    source = open(os.path.join(TOOLS, name + ".py"), encoding="utf-8").read()
    assert "json.dump" in source or "open(" in source


@pytest.mark.parametrize("name", SCRIPT)
def test_usage_lines_promise_no_missing_flags(name):
    """Se il docstring documenta --qualcosa, il codice deve leggerlo davvero."""
    source = open(os.path.join(TOOLS, name + ".py"), encoding="utf-8").read()
    doc = ast.get_docstring(ast.parse(source)) or ""
    promised = set(re.findall(r"(?<![\w-])(--[a-z][a-z-]+)", doc))
    read_flags = set(re.findall(r'"(--[a-z][a-z-]+)"', source))
    assert promised <= read_flags, f"{name}.py documenta {sorted(promised - read_flags)} e non li legge"
