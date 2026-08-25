"""revise.py: la revisione esterna che rientra nel dizionario.

Il rischio qui non e' una segnalazione sbagliata, e' una correzione applicata
alla stringa sbagliata. Fra il pacchetto che parte e la risposta che torna il
dizionario si muove, e sovrascrivere una resa cambiata nel frattempo cancella
in silenzio proprio il lavoro piu' recente: e' l'unica cosa che questi test
guardano da tre angoli diversi.

Come tutti gli strumenti che scrivono, si prova puntato a una cartella
temporanea: il dizionario vero non si tocca.
"""
import json
import os

import pytest

from conftest import tool

RV = tool("revise")


def finding(en, before, after, **extra):
    base = {"en": en, "it_attuale": before, "it_proposto": after,
            "categoria": "grammatica", "gravita": "media", "perche": "una ragione"}
    base.update(extra)
    return base


@pytest.fixture
def review(tmp_path):
    """Un JSONL di revisione, scritto come lo scrive chi rilegge."""
    def write(*items):
        p = tmp_path / "revisione.jsonl"
        p.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items),
                     encoding="utf-8")
        return str(p)
    return write


@pytest.fixture
def dictionary_at(tmp_path, monkeypatch):
    """Un dizionario finto, e revise.py puntato li'."""
    def write(strings):
        p = tmp_path / "it.json"
        p.write_text(json.dumps({"overrides": {}, "strings": strings}, ensure_ascii=False),
                     encoding="utf-8")
        monkeypatch.setattr(RV, "DICT", str(p))
        return p
    return write


# --- il controllo che giustifica lo strumento ------------------------------
def test_a_string_that_moved_since_the_review_is_never_overwritten(review, dictionary_at):
    """La deriva e' il caso per cui esiste il confronto con it_attuale."""
    p = dictionary_at({"A book": "Un tomo"})          # nel frattempo e' cambiata
    items = RV.load(review(finding("A book", "Un libro", "Un volume")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(), {})
    assert items[0]["stato"] == "deriva"
    RV.apply_findings(items, {})
    assert json.loads(p.read_text(encoding="utf-8"))["strings"]["A book"] == "Un tomo"


def test_a_matching_string_is_corrected(review, dictionary_at):
    p = dictionary_at({"A book": "Un libro"})
    items = RV.load(review(finding("A book", "Un libro", "Un volume")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(), {})
    assert items[0]["stato"] == "applicabile"
    RV.apply_findings(items, {})
    assert json.loads(p.read_text(encoding="utf-8"))["strings"]["A book"] == "Un volume"


def test_two_findings_on_one_string_do_not_stack(review, dictionary_at):
    """La seconda lavorerebbe su un testo che la prima ha gia' cambiato."""
    p = dictionary_at({"A book": "Un libro"})
    items = RV.load(review(finding("A book", "Un libro", "Un volume"),
                           finding("A book", "Un libro", "Un tomo")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(), {})
    done = RV.apply_findings(items, {})
    assert len(done) == 1
    assert json.loads(p.read_text(encoding="utf-8"))["strings"]["A book"] == "Un volume"


def test_the_gates_hold_a_finding_back(review, dictionary_at):
    p = dictionary_at({"A book": "Un libro"})
    items = RV.load(review(finding("A book", "Un libro", "Un volume")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(), {})
    RV.apply_findings(items, {items[0]["origine"]: "glossario"})
    assert json.loads(p.read_text(encoding="utf-8"))["strings"]["A book"] == "Un libro"


def test_the_dictionary_keeps_its_shape(review, dictionary_at):
    """overrides non si perde, e le chiavi restano ordinate come le scrive prose.py."""
    p = dictionary_at({"B": "Bi", "A": "A"})
    items = RV.load(review(finding("A", "A", "Alfa")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(), {})
    RV.apply_findings(items, {})
    after = json.loads(p.read_text(encoding="utf-8"))
    assert "overrides" in after
    assert list(after["strings"]) == sorted(after["strings"])


# --- il registro delle decisioni gia' prese --------------------------------
def test_a_rejected_finding_is_not_proposed_again(review, dictionary_at):
    p = dictionary_at({"A book": "Un libro"})
    items = RV.load(review(finding("A book", "Un libro", "Un volume")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"], set(),
                {"A book": "«volume» e' un'altra cosa"})
    assert items[0]["stato"] == "respinta"
    RV.apply_findings(items, {})
    assert json.loads(p.read_text(encoding="utf-8"))["strings"]["A book"] == "Un libro"


def test_rejecting_writes_the_reason_down(tmp_path, monkeypatch, review):
    monkeypatch.setattr(RV, "REJECTED", str(tmp_path / "respinte.json"))
    items = RV.load(review(finding("A book", "Un libro", "Un volume")))
    RV.reject(items, "la ragione dello scarto")
    written = json.loads((tmp_path / "respinte.json").read_text(encoding="utf-8"))
    assert written["A book"] == "la ragione dello scarto"
    assert written["_nota"], "il registro deve dire a che cosa serve, come gli altri tre"


# --- la lettura del file della revisione -----------------------------------
def test_a_finding_without_its_fields_is_refused(tmp_path):
    p = tmp_path / "rotta.jsonl"
    p.write_text(json.dumps({"en": "A book", "it_proposto": "Un volume"}), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        RV.load(str(p))
    assert "it_attuale" in str(e.value)


def test_a_line_that_is_not_json_says_which_one(tmp_path):
    p = tmp_path / "rotta.jsonl"
    good = json.dumps({"en": "A book", "it_attuale": "Un libro", "it_proposto": "Un volume",
                       "categoria": "grammatica", "gravita": "media", "perche": "x"})
    p.write_text(good + "\nnon sono json\n", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        RV.load(str(p))
    assert ":2" in str(e.value)


# --- l'ampiezza, che e' il criterio per lavorare in blocco ------------------
@pytest.mark.parametrize("before,after,expected", [
    ("Un libro.", "Un libro,", "punteggiatura"),
    ("Un libro di ore", "Il libro delle ore", "funzionali"),
    ("Un libro di ore", "Un tomo di ore", "corte"),
    ("Il gatto dorme sul davanzale caldo", "Il felino riposa sopra la finestra tiepida", "medie"),
])
def test_width_tells_a_comma_from_a_rewrite(before, after, expected):
    assert RV.width(before, after) == expected


def test_scattered_small_changes_are_not_a_small_change():
    """Cinque parole cambiate in cinque punti diversi restano cinque parole."""
    before = "Il primo e il secondo e il terzo e il quarto e il quinto"
    after = "Un primo e un secondo e un terzo e un quarto e un quinto"
    assert RV.width(before, after) != "corte"


def test_ui_labels_are_told_apart_from_the_dictionary(review, dictionary_at):
    """Le 52 label d'interfaccia non stanno nel dizionario: vanno per un'altra strada."""
    p = dictionary_at({"A book": "Un libro"})
    items = RV.load(review(finding("$Go to Threshold", "Vai alla Soglia", "Alla Soglia")))
    RV.classify(items, json.loads(p.read_text(encoding="utf-8"))["strings"],
                {"$Go to Threshold"}, {})
    assert items[0]["stato"] == "interfaccia"
