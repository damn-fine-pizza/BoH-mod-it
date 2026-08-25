"""Il pacchetto e i suoi contorni: pack, sources, prereqs, savegame, signs.

pack.py e' l'unico strumento che decide che cosa esce dal repository, e le due
cose che deve fare bene sono la lista di cio' che entra e il rifiuto di
ricostruire uno zip che esiste gia'. savegame.py e' l'unico che tocca file di
qualcun altro - le partite salvate - e deve sostituire solo dove il testo
inglese e' esattamente una chiave del dizionario.
"""
import json
import os

import pytest

from conftest import tool

K = tool("pack")
SO = tool("sources")
PR = tool("prereqs")
SG = tool("savegame")
SI = tool("signs")


# --- pack -----------------------------------------------------------------

def test_sizes_read_at_a_glance():
    assert K.mb(1500) == "1 KB"
    assert K.mb(2 * 1024 * 1024) == "2.0 MB"


def test_folder_weight_is_the_sum_of_its_files(tmp_path):
    (tmp_path / "a").write_bytes(b"x" * 100)
    (tmp_path / "sotto").mkdir()
    (tmp_path / "sotto" / "b").write_bytes(b"y" * 50)
    assert K.weight(str(tmp_path)) == 150


def test_the_synopsis_comes_from_the_metadata():
    meta = {"name": "X", "author": "Y", "version": "9.9.9",
            "description_short": "corta", "description_long": "lunga"}
    s = K.synopsis(meta)
    assert s["version"] == "9.9.9" and s["name"] == "X"


def test_the_package_allowlist_is_explicit():
    """Si copia da una lista di cose ammesse: una cartella nuova resta fuori
    finche' qualcuno non decide che ci deve stare."""
    allowed = {x[0] for x in K.ALLOWED}
    assert allowed == {"content", "images", "loc/loc_it", "cover.png"}


def test_reference_material_stays_out_of_the_package():
    """13 MB di mod francese e originale inglese servono a chi traduce, non a chi gioca."""
    allowed = {x[0] for x in K.ALLOWED}
    assert not any(x.startswith("loc/_") for x in allowed)


def test_the_synopsis_is_generated_not_copied():
    """Scriverlo a mano vuol dire vederlo sovrascritto al primo pack."""
    assert "synopsis.json" in K.GENERATED


# --- sources --------------------------------------------------------------

def test_only_png_files_are_counted(tmp_path):
    (tmp_path / "a.png").write_bytes(b"")
    (tmp_path / "b.txt").write_bytes(b"")
    assert SO.count_of(str(tmp_path)) == 1


def test_a_missing_folder_counts_zero():
    assert SO.count_of("/non/esiste/proprio") == 0


def test_the_weather_factory_zip_is_the_public_one():
    """Se cambia l'indirizzo, il ripristino dell'arte smette di funzionare in
    silenzio: meglio che sia un test a dirlo."""
    assert SO.ZIP.startswith("https://weatherfactory.biz/") and SO.ZIP.endswith(".zip")


# --- prereqs --------------------------------------------------------------

def test_an_installed_package_is_found():
    assert PR.version("pytest") is not None


def test_a_missing_package_returns_none():
    assert PR.version("questo-pacchetto-non-esiste-42") is None


def test_module_name_sees_importable_modules():
    assert PR.module_name("json") is True
    assert PR.module_name("modulo_che_non_esiste_42") is False


def test_the_prerequisites_are_grouped():
    groups = {r[0] for r in PR.collect()}
    assert "per il testo" in groups and "per le copertine" in groups


# --- savegame -------------------------------------------------------------

def test_only_exact_dictionary_keys_are_replaced():
    import collections
    d = {"Post Office Counter": "Bancone dell'Ufficio Postale"}
    save = {"RootPopulationCommand": {"Spheres": [
        {"Label": "Post Office Counter"},
        {"Label": "Post Office Counter, closed"},     # non e' la chiave: non si tocca
    ]}}
    count, examples = collections.Counter(), []
    SG.translate(save, d, count, examples)
    spheres = save["RootPopulationCommand"]["Spheres"]
    assert spheres[0]["Label"] == "Bancone dell'Ufficio Postale"
    assert spheres[1]["Label"] == "Post Office Counter, closed"
    assert count["Label"] == 1


def test_only_text_fields_are_touched():
    """Label, Description, Desc, StartDescription: non gli id, non le quantita'."""
    import collections
    d = {"Post Office Counter": "Bancone"}
    save = {"Id": "Post Office Counter", "Label": "Post Office Counter"}
    SG.translate(save, d, collections.Counter(), [])
    assert save["Id"] == "Post Office Counter" and save["Label"] == "Bancone"


def test_nested_lists_are_walked():
    import collections
    d = {"A": "B"}
    save = [[{"Label": "A"}]]
    SG.translate(save, d, collections.Counter(), [])
    assert save[0][0]["Label"] == "B"


def test_the_reverse_dictionary_skips_ambiguous_renderings():
    """«Enquire» e «Investigate» possono finire tutt'e due su «Indaga»: da li'
    non si torna indietro, e indovinare sarebbe peggio del problema."""
    r = SG.reverse({"Enquire": "Indaga", "Investigate": "Indaga",
                    "The Iron Book": "Il Libro di Ferro"})
    assert r == {"Il Libro di Ferro": "The Iron Book"}


def test_the_reverse_dictionary_skips_untranslated_strings():
    """Se la resa e' identica all'inglese non c'e' niente da rimettere."""
    assert SG.reverse({"Ereb": "Ereb"}) == {}


def test_english_is_put_back_into_a_save():
    import collections
    d = SG.reverse({"Post Office Counter": "Bancone dell'Ufficio Postale"})
    save = {"Spheres": [{"Label": "Bancone dell'Ufficio Postale"}]}
    SG.translate(save, d, collections.Counter(), [])
    assert save["Spheres"][0]["Label"] == "Post Office Counter"


# --- signs ----------------------------------------------------------------

def test_lines_of_finds_text_rows_in_a_label():
    """Le insegne si rifanno misurando l'originale: quante righe, quanto alte."""
    import numpy as np
    alpha = np.zeros((30, 40), np.uint8)
    alpha[2:14, 5:35] = 255                # una riga di scritta, alta dodici pixel
    alpha[18:30, 5:35] = 255               # e un'altra
    assert len(SI.lines_of(alpha, 16)) == 2


def test_lines_of_ignores_bands_too_thin():
    """Sotto gli otto pixel non e' una riga di testo: e' il bordo della targa."""
    import numpy as np
    alpha = np.zeros((30, 40), np.uint8)
    alpha[5:8, 5:35] = 255
    assert SI.lines_of(alpha, 16) == []
