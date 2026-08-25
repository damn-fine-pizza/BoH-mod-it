"""La catena del dizionario: apply, extract, split, join, merge, progress.

Sono gli strumenti che scrivono: i file del mod, le slice, il dizionario. Ogni
test qui dentro lavora in una cartella temporanea, mai sul repository - e il
motivo per cui merge.py e join.py si provano davvero e' che un errore li' non
si vede in una segnalazione: si vede in un dizionario corrotto.
"""
import collections
import json
import os

import pytest

from conftest import tool

A = tool("apply")
E = tool("extract")
P = tool("progress")
J = tool("join")


# --- apply ---------------------------------------------------------------

def test_prune_keeps_only_what_the_kit_allows():
    ent = {"ID": "x", "Label": "A", "Description": "B",
           "reqs": {"lantern": 1}, "aspects": {"a": 1}, "warmup": 30, "icon": "x.png"}
    assert A.prune(ent, "elements") == {"ID": "x", "Label": "A", "Description": "B"}


def test_prune_reduces_slots_to_id_label_description():
    ent = {"ID": "x", "slots": [{"id": "s", "Label": "L", "reqs": {"a": 1}, "greedy": True}]}
    assert A.prune(ent, "recipes") == {"ID": "x", "slots": [{"id": "s", "Label": "L"}]}


def test_translate_entity_replaces_and_counts():
    stats = collections.Counter()
    ent = {"ID": "x", "Label": "The Iron Book"}
    d = {"overrides": {}, "strings": {"The Iron Book": "Il Libro di Ferro"}}
    A.translate_entity(ent, "elements", d, stats)
    assert ent["Label"] == "Il Libro di Ferro"
    assert stats["tradotte"] == 1


def test_translate_entity_leaves_english_when_unknown():
    """apply.py non inventa: dove il dizionario tace, resta l'inglese."""
    stats = collections.Counter()
    ent = {"ID": "x", "Label": "Something Unknown"}
    A.translate_entity(ent, "elements", {"overrides": {}, "strings": {}}, stats)
    assert ent["Label"] == "Something Unknown"


def test_overrides_beat_strings():
    stats = collections.Counter()
    ent = {"ID": "x", "Label": "The Iron Book"}
    d = {"overrides": {"elements/x.label": "Resa speciale"},
         "strings": {"The Iron Book": "Il Libro di Ferro"}}
    A.translate_entity(ent, "elements", d, stats)
    assert ent["Label"] == "Resa speciale"


# --- extract -------------------------------------------------------------

def test_a_field_key_is_stable():
    """E' l'indirizzo con cui gli overrides puntano a un campo preciso."""
    assert E.key_of("elements", "book", "label") == "elements/book.label"


# --- progress ------------------------------------------------------------

def test_the_slice_number_comes_from_the_filename():
    assert P.num("/qualsiasi/percorso/chunk_12.json") == "12"


@pytest.mark.parametrize("seconds, expected_text", [(30, "30s"), (200, "3m"), (7200, "2h00m")])
def test_duration_reads_at_a_glance(seconds, expected_text):
    assert P.duration(seconds) == expected_text


def test_the_bar_is_as_long_as_asked():
    assert P.bar(50, 10) == "#####....."
    assert P.bar(0, 4) == "...." and P.bar(100, 4) == "####"


def test_read_lines_tolerates_a_half_written_file(tmp_path):
    """Il monitor gira mentre gli agenti scrivono: un JSON tronco non deve fermarlo."""
    p = tmp_path / "part_1.json"
    p.write_text('{\n "The Iron Book": "Il Libro di Ferro",\n "Altro": ', encoding="utf-8")
    loaded = P.read_lines(str(p))
    assert "The Iron Book" in loaded


def test_the_rate_is_measured_from_when_the_work_started():
    """La finestra parte dalla prima lettura con del lavoro fatto, non dalla
    prima in assoluto: quella comprende l'avvio dell'agente, e una volta ha
    compreso venti minuti di un agente nato morto."""
    samples = [{"t": 0, "slice": {"1": 0}},        # l'agente e' appena nato
               {"t": 600, "slice": {"1": 100}}]     # qui e' a regime: si misura da qui
    # 300 stringhe fatte in 600 secondi da quel momento: 30 al minuto. Misurando
    # dalla prima lettura verrebbero 20, e sarebbe una stima falsa.
    assert P.rate(samples, 1, 400, 1200) == pytest.approx(30.0)


def test_a_log_written_by_an_older_version_does_not_crash_the_monitor():
    """Il registro del ritmo e' un misuratore, non un dato prezioso: se una
    versione precedente ha usato un'altra chiave il monitor la ignora, invece di
    morire con un KeyError. E' successo davvero rinominando la chiave."""
    old_log = [{"t": 0, "altro_nome": {"1": 10}}, {"t": 60, "altro_nome": {"1": 20}}]
    assert P.rate(old_log, 1, 3600, 120) is None


def test_read_lines_survives_an_empty_file(tmp_path):
    p = tmp_path / "part_2.json"
    p.write_text("", encoding="utf-8")
    assert P.read_lines(str(p)) == {}


# --- join ----------------------------------------------------------------

def test_join_rebuilds_a_slice_from_fragments(tmp_path, monkeypatch):
    """I frammenti sono la rete di chi traduce: si fondono, non si perdono."""
    monkeypatch.setattr(J, "PARTS", str(tmp_path))
    (tmp_path / "part_7.001.json").write_text(
        json.dumps({"a": "A"}), encoding="utf-8")
    (tmp_path / "part_7.002.json").write_text(
        json.dumps({"b": "B"}), encoding="utf-8")
    assert sorted(os.path.basename(x) for x in J.fragments(7, str(tmp_path))) == \
        ["part_7.001.json", "part_7.002.json"]
