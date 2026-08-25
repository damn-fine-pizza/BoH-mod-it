"""Le sigle sui dorsi e la forma dei titoli.

La sigla e' l'unica cosa che il giocatore legge sul dorso di un libro, e il kit
la vincola: «short, 1-4 character titles in the target language», con lo scopo
di far ricordare quale libro sia quale. Le regole qui sotto sono la ragione per
cui «Vangelo di Nicodemo» da' VdN come l'inglese da' GoN.
"""
import pytest

from conftest import tool

I = tool("initials")
B = tool("booktitles")
T = tool("titles")


@pytest.mark.parametrize("title, expected", [
    ("Vangelo di Nicodemo", "VdN"),            # maiuscola alle piene, minuscola alle funzionali
    ("Nefrite Nera", "NN"),
    ("Esorcismo per Ragazze", "EpR"),
    ("Una Discesa del Guscio", "UDdG"),        # la prima e' sempre maiuscola, anche se articolo
    ("Un Catalogo di Piaceri Inesplorati", "UCdPI"),
])
def test_initials_follow_the_english_scheme(title, expected):
    assert I.initials(title) == expected


def test_an_apostrophe_separates_two_words():
    """«L'Eco di Silenzio» sono quattro parole, non tre: L, Eco, di, Silenzio."""
    assert I.initials("L'Eco di Silenzio") == "LEdS"


def test_the_exclamation_mark_survives():
    assert I.initials("Ambrosiaco!") == "A!"


def test_initials_never_exceed_the_cap():
    long_title = "Le Mie Gesta i Miei Poteri i Miei Successi e le Ingiustizie Perpetrate Contro di Me"
    assert len(I.initials(long_title)) <= I.CAP if hasattr(I, "CAP") else len(I.initials(long_title)) <= 6


def test_the_volume_number_leaves_the_base_and_turns_roman():
    """Senza questo i tre De Horis avevano tutti la stessa sigla."""
    base, marker, qualifier = I.decompose("De Horis, libro 1", "De Horis book 1")
    assert (base, marker) == ("De Horis", "I")


def test_the_qualifier_joins_the_initials_without_eating_the_title():
    """La forma attuale e' «I Tre e i Tre (Manoscritto di Kerisham)»: dentro le
    parentesi c'e' la qualificazione, non la traduzione."""
    base, _, qualifier = I.decompose("I Tre e i Tre (Manoscritto di Kerisham)",
                                          "The Three and the Three (Kerisham Manuscript)")
    assert base == "I Tre e i Tre"
    assert qualifier == "Manoscritto di Kerisham"


def test_the_year_becomes_the_marker():
    _, marker, _ = I.decompose("Diario di Sir David Greene, 1903",
                                  "Journal of Sir David Greene, 1903")
    assert marker == "1903"


def test_last_word_takes_the_last_full_word():
    assert I.last_word("Il Libro di Ferro") == "Ferro"


def test_titles_reduce_to_the_italian_form_alone():
    """La forma bilingue «EN (IT)» e' stata abbandonata: resta solo l'italiano."""
    assert T.disassemble("The Iron Book (Il Libro di Ferro)", "The Iron Book") == "Il Libro di Ferro"


def test_titles_return_none_when_nothing_to_change():
    """None vuol dire «niente da cambiare»: il titolo e' gia' nella forma buona."""
    assert T.disassemble("Il Libro di Ferro", "The Iron Book") is None


def test_titles_leave_parentheses_that_belong_to_the_italian_title():
    """Se la testa non e' il titolo inglese, quelle parentesi fanno parte della resa."""
    assert T.disassemble("I Tre e i Tre (Manoscritto di Kerisham)", "The Iron Book") is None


def test_booktitles_split_volume_and_qualifier():
    """Il volume si stacca solo dopo una virgola: «De Horis book 1», senza, e' tutto titolo."""
    assert B.decompose("De Horis, book 1") == ("De Horis", None, "book 1")
    assert B.decompose("De Horis book 1") == ("De Horis book 1", None, None)
    assert B.decompose("The Three and the Three (Kerisham Manuscript)") == \
        ("The Three and the Three", "Kerisham Manuscript", None)
