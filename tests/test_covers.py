"""Le copertine: covers, plates, index, cover.

covers.area e' il punto delicato di tutta la catena delle immagini: ricava dove
stava la scritta inglese confrontando la lastra ripulita con l'originale, e da
li' prende anche il colore dell'inchiostro. Se sbaglia il riquadro, la sigla
italiana finisce fuori posto su 244 copertine e nessun controllo se ne accorge,
perche' il file c'e' comunque.
"""
import numpy as np
import pytest
from PIL import Image

from conftest import tool

C = tool("covers")
PL = tool("plates")
IX = tool("index")


def fake_cover(with_text=True):
    orig = Image.new("RGB", (40, 20), (200, 180, 160))
    plate = orig.copy()
    if with_text:
        for x in range(10, 20):
            orig.putpixel((x, 8), (20, 20, 20))
    return orig, plate


def test_area_finds_the_box_of_the_erased_text():
    orig, plate = fake_cover()
    bb, colour = C.area(orig, plate)
    assert bb == (10, 8, 20, 9)


def test_area_takes_the_ink_colour_from_the_original():
    orig, plate = fake_cover()
    _, colour = C.area(orig, plate)
    assert colour == (20, 20, 20)


def test_area_says_nothing_when_the_plate_is_identical():
    """Nessuna differenza vuol dire nessuna scritta cancellata: non si inventa."""
    _, plate = fake_cover()
    assert C.area(plate, plate) == (None, None)


def test_area_ignores_differences_below_the_threshold():
    """Il ricampionamento lascia scarti di un paio di livelli: non sono testo."""
    orig = Image.new("RGB", (10, 10), (200, 200, 200))
    plate = Image.new("RGB", (10, 10), (203, 203, 203))
    assert C.area(orig, plate, threshold=16)[0] is None


def test_write_draws_inside_the_box_and_reports_how():
    img = Image.new("RGB", (60, 30), (200, 180, 160))
    size, rows = C.write(img, (5, 5, 55, 25), "VdN", (20, 20, 20))
    assert size > 0 and rows >= 1
    assert img.getcolors(4096) != Image.new("RGB", (60, 30), (200, 180, 160)).getcolors(4096)


def test_write_splits_the_initials_in_balanced_lines():
    """Riempire avidamente la prima riga lascia un avanzo storto.

    Sul dorso quadrato di «Una Torre Sorge» la sigla UTS veniva spezzata UT|S,
    mentre l'inglese spezza ᴀ|TR. Ora si cerca la ripartizione che rende piu'
    stretta la riga piu' larga, e viene U|TS.
    """
    img = Image.new("RGB", (30, 30), (240, 235, 225))
    C.write(img, (2, 2, 28, 28), "UTS", (20, 20, 20))
    # la riga di sopra deve avere meno inchiostro di quella di sotto: U contro TS
    px = img.load()
    meta = 15
    sopra = sum(1 for y in range(2, meta) for x in range(2, 28) if px[x, y][0] < 128)
    sotto = sum(1 for y in range(meta, 28) for x in range(2, 28) if px[x, y][0] < 128)
    assert sopra < sotto, "la sigla e' ancora spezzata con la riga lunga in cima"


def test_the_manifest_is_indexed_by_id():
    man = C.manifest()
    assert "t.theironbook" in man and man["t.theironbook"]["it"]


# --- plates ---------------------------------------------------------------

def test_components_finds_ink_blobs():
    m = np.zeros((10, 10), bool)
    m[2:5, 2:5] = True                      # nove pixel: un grumo vero
    assert len(PL.components(m)) == 1


def test_components_ignores_specks():
    """Sotto i sei pixel e' rumore di ricampionamento, non inchiostro."""
    m = np.zeros((10, 10), bool)
    m[1, 1] = m[1, 2] = True
    assert PL.components(m) == []


def test_small_components_keeps_only_the_small_ones():
    m = np.zeros((10, 10), bool)
    m[1, 1] = True
    m[5:9, 5:9] = True
    small_ones = PL.small_components(m, 4)
    assert small_ones[1, 1] and not small_ones[6, 6]


def test_align_finds_the_offset_between_sprites_of_different_height():
    """Iron, Ivory e Silver hanno lo sprite inglese quattro pixel piu' alto:
    senza allineamento il confronto veniva saltato e restavano senza sigla."""
    english = np.zeros((24, 10, 3), np.uint8)      # lo sprite EN, quattro px piu' alto
    english[10:14, 3:7] = 255
    other_language = np.zeros((20, 10, 3), np.uint8)  # la stessa figura, sprite piu' corto
    other_language[8:12, 3:7] = 255
    aligned = PL._align(Image.fromarray(english), Image.fromarray(other_language))
    assert aligned is not None and aligned.size == (10, 24)


def test_align_refuses_a_sprite_larger_than_the_english_one():
    """Piu' grande vuol dire che non e' lo stesso disegno: meglio non confrontarli."""
    small = Image.fromarray(np.zeros((10, 10, 3), np.uint8))
    large = Image.fromarray(np.zeros((20, 20, 3), np.uint8))
    assert PL._align(small, large) is None


# --- index ----------------------------------------------------------------

def test_plate_state_reports_which_books_have_a_plate():
    state = IX.plate_state([{"id": "t.theironbook", "testo": True, "stato": "tradotto"}])
    assert isinstance(state, dict)
