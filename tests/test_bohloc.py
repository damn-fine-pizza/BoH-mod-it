"""Il lettore JSON e i percorsi.

bohloc.read e' la base di tutto: se sbaglia a leggere un file del gioco, ogni
conteggio a valle e' falso e nessuno se ne accorge, perche' il numero esce
comunque. I file del core non sono JSON pulito - ci sono virgole finali, UTF-16
con BOM, caratteri di controllo dentro le stringhe - e le tre strade di ripiego
sono la ragione per cui questo modulo esiste.
"""
import json
import os

import pytest

from conftest import tool

b = tool("bohloc")


def write_file(tmp_path, with_text, name="x.json", encoding="utf-8"):
    p = tmp_path / name
    p.write_bytes(with_text.encode(encoding))
    return str(p)


def test_reads_plain_json(tmp_path):
    assert b.read(write_file(tmp_path, '{"a": 1}')) == {"a": 1}


def test_reads_utf16_with_bom(tmp_path):
    """Meta' dei file del core sono UTF-16: senza questo ramo si legge spazzatura."""
    assert b.read(write_file(tmp_path, '{"a": "è"}', encoding="utf-16")) == {"a": "è"}


def test_reads_utf8_with_bom(tmp_path):
    assert b.read(write_file(tmp_path, '﻿{"a": 1}')) == {"a": 1}


def test_tolerates_a_trailing_comma(tmp_path):
    assert b.read(write_file(tmp_path, '{"a": 1,}')) == {"a": 1}


def test_tolerates_control_characters(tmp_path):
    """L'ultima spiaggia: strict=False, che accetta un a-capo dentro una stringa."""
    output = b.read(write_file(tmp_path, '{"a": "riga\nriga",}'))
    assert output["a"].startswith("riga")


def test_entities_takes_top_level_entities():
    data = {"elements": [{"id": "x", "Label": "A"}, {"id": "y"}], "altro": "non una lista"}
    assert b.entities(data) == [("elements", {"id": "x", "Label": "A"}), ("elements", {"id": "y"})]


def test_strings_of_takes_translatable_fields():
    ent = {"id": "x", "Label": "A", "Description": "B", "reqs": {"lantern": 1}}
    assert b.strings_of(ent) == {"label": "A", "description": "B"}


def test_strings_of_sees_the_singular_slot():
    """Il caso dell'Ufficio Postale: «slot» al singolare, 29 stringhe mai estratte."""
    ent = {"id": "x", "slot": {"id": "s1", "Label": "Post Office Counter"}}
    assert b.strings_of(ent) == {"slot.s1.label": "Post Office Counter"}


def test_strings_of_sees_preslots():
    ent = {"id": "x", "preslots": [{"id": "p1", "Label": "Repairs"}]}
    assert b.strings_of(ent) == {"preslots.p1.label": "Repairs"}


def test_strings_of_sees_xexts():
    ent = {"id": "x", "xexts": {"page1": "testo"}}
    assert b.strings_of(ent) == {"xexts.page1": "testo"}


def test_strings_of_ignores_game_logic():
    ent = {"id": "x", "aspects": {"lantern": 1}, "warmup": 30, "icon": "x.png"}
    assert b.strings_of(ent) == {}


def test_load_tree_indexes_by_category_and_id(tmp_path):
    (tmp_path / "elements").mkdir()
    (tmp_path / "elements" / "a.json").write_text(
        json.dumps({"elements": [{"id": "book", "Label": "The Iron Book"}]}), encoding="utf-8")
    index, *_ = b.load_tree(str(tmp_path))
    assert index[("elements", "book")]["strings"] == {"label": "The Iron Book"}


def test_path_for_prefers_the_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("BOH_TEST_PATH", str(tmp_path))
    assert b.path_for("test_path", "/non/esiste") == str(tmp_path)


def test_path_for_takes_the_first_that_exists(tmp_path, monkeypatch):
    monkeypatch.delenv("BOH_TEST_PATH", raising=False)
    assert b.path_for("test_path", "/non/esiste/proprio", str(tmp_path)) == str(tmp_path)


def test_path_for_keeps_the_first_when_none_exist(monkeypatch):
    """Meglio un percorso sbagliato sotto gli occhi che una stringa vuota."""
    monkeypatch.delenv("BOH_TEST_PATH", raising=False)
    assert b.path_for("test_path", "/non/esiste/a", "/non/esiste/b") == "/non/esiste/a"


def test_project_paths_stay_inside_the_repository():
    assert os.path.isdir(b.MOD) and b.MOD.startswith(b.PROJ)
    assert b.IT.startswith(b.MOD)
