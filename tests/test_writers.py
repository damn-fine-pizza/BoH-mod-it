"""Gli strumenti che scrivono: split e merge.

Un errore qui non produce una segnalazione: produce un dizionario sbagliato, o
una slice che si sovrappone a un'altra e fa tradurre due volte la stessa
stringa a due agenti diversi. Si provano puntandoli a cartelle temporanee.
"""
import collections
import json
import os

import pytest

from conftest import tool

SP = tool("split")
MG = tool("merge")


@pytest.fixture
def to_translate():
    """La forma che pending() restituisce: testo -> [(file, chiave)]."""
    return collections.OrderedDict(
        (f"String number {i}", [("elements/abilities.json", f"elements/e{i}.label")])
        for i in range(1, 11))


def test_split_makes_slices_that_never_overlap(tmp_path, monkeypatch, to_translate):
    monkeypatch.setattr(SP, "PROJ", str(tmp_path))
    monkeypatch.setattr(SP, "pending", lambda *a, **k: to_translate)
    SP.main(2, 3)
    parts = tmp_path / "translations" / "parts"
    first_slice = json.loads((parts / "chunk_1.json").read_text(encoding="utf-8"))
    second_slice = json.loads((parts / "chunk_2.json").read_text(encoding="utf-8"))
    assert len(first_slice) == 3 and len(second_slice) == 3
    assert not {x["en"] for x in first_slice} & {x["en"] for x in second_slice}


def test_split_resumes_where_it_stopped(tmp_path, monkeypatch, to_translate):
    """Senza --offset le stringhe gia' assegnate finirebbero a un secondo agente."""
    monkeypatch.setattr(SP, "PROJ", str(tmp_path))
    monkeypatch.setattr(SP, "pending", lambda *a, **k: to_translate)
    SP.main(1, 3)
    SP.main(1, 3, offset=3, first=2)
    parts = tmp_path / "translations" / "parts"
    first_slice = json.loads((parts / "chunk_1.json").read_text(encoding="utf-8"))
    second_slice = json.loads((parts / "chunk_2.json").read_text(encoding="utf-8"))
    assert not {x["en"] for x in first_slice} & {x["en"] for x in second_slice}


def test_split_records_where_a_string_lives_and_how_often(tmp_path, monkeypatch,
                                                                 to_translate):
    """Chi traduce ha bisogno del contesto: il file di provenienza e la frequenza."""
    monkeypatch.setattr(SP, "PROJ", str(tmp_path))
    monkeypatch.setattr(SP, "pending", lambda *a, **k: to_translate)
    SP.main(1, 1)
    entry = json.loads((tmp_path / "translations" / "parts" / "chunk_1.json")
                      .read_text(encoding="utf-8"))[0]
    assert set(entry) == {"en", "dove", "ricorre"}


def prepare_merge(tmp_path, monkeypatch, parte, dizionario=None):
    parts = tmp_path / "parts"
    parts.mkdir()
    (parts / "part_1.json").write_text(json.dumps(parte, ensure_ascii=False), encoding="utf-8")
    d = tmp_path / "it.json"
    d.write_text(json.dumps(dizionario or {"overrides": {}, "strings": {}},
                            ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(MG, "PARTS", str(parts))
    monkeypatch.setattr(MG, "DICT", str(d))
    monkeypatch.setattr(MG, "load_tree", lambda *a, **k: (
        {("elements", "e1"): {"file": "elements/a.json",
                              "strings": {"label": "The Iron Book"}}}, [], []))
    return d


def test_merge_folds_a_slice_into_the_dictionary(tmp_path, monkeypatch):
    d = prepare_merge(tmp_path, monkeypatch, {"The Iron Book": "Il Libro di Ferro"})
    MG.main()
    assert json.loads(d.read_text(encoding="utf-8"))["strings"]["The Iron Book"] == \
        "Il Libro di Ferro"


def test_merge_in_dry_mode_writes_nothing(tmp_path, monkeypatch):
    d = prepare_merge(tmp_path, monkeypatch, {"The Iron Book": "Il Libro di Ferro"})
    MG.main(dry=True)
    assert json.loads(d.read_text(encoding="utf-8"))["strings"] == {}


def test_merge_catches_orphans(tmp_path, monkeypatch, capsys):
    """Una resa la cui chiave inglese non esiste nel gioco: quasi sempre e' un
    inglese ricopiato male, e senza questo controllo entrerebbe nel dizionario."""
    d = prepare_merge(tmp_path, monkeypatch, {"Non esiste nel core": "Qualcosa"})
    MG.main()
    output = capsys.readouterr().out
    assert "non combaciano" in output
    assert "Non esiste nel core" not in json.loads(d.read_text(encoding="utf-8"))["strings"]
