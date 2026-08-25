"""I cancelli sul testo: logic, checkpart, identical, grammar, validate.

Sono i controlli che decidono se il mod si pubblica. Ognuno ha una zona grigia,
e i casi qui sotto sono quelli in cui una versione precedente sbagliava: il
genitivo sassone contato come virgoletta aperta, il nome proprio scambiato per
resa mancante, la stringa uguale all'inglese che era una scelta e non un buco.
"""
import pytest

from conftest import tool

L = tool("logic")
C = tool("checkpart")
I = tool("identical")


# --- logic ---------------------------------------------------------------

def test_digits_are_counted_by_value():
    assert L.digits("1451-1551 e 7 volte") == {"1451": 1, "1551": 1, "7": 1}


def test_the_saxon_genitive_is_not_a_quote():
    """Contarlo dava 36 segnalazioni su 36 sbagliate."""
    assert L.quotation_marks("Yvette's book") == 0
    assert L.quotation_marks("don't") == 0
    assert L.quotation_marks("Ys' house") == 0


def test_a_real_quote_is_counted():
    assert L.quotation_marks("'una citazione'") == 2


def test_clean_strips_tags_and_tokens():
    assert L.clean("<i>ciao</i> {SPHERE:x}").strip() == "ciao"


# --- checkpart -----------------------------------------------------------

def test_real_words_exclude_tags_and_aspect_ids():
    assert C._words("<i>Il</i> {ASPECT:lantern} cielo") == ["Il", "cielo"]


def test_proper_nouns_mid_sentence_are_not_missing_renderings():
    """Restano in inglese per convenzione: Janus, non Giano."""
    assert "janus" in C._proper_nouns("The road to Janus is long")


def test_the_first_word_of_a_sentence_is_not_a_proper_noun():
    """E' maiuscola perche' apre la frase, non perche' e' un nome."""
    assert "the" not in C._proper_nouns("The road is long")


# --- identical -----------------------------------------------------------

def test_normalize_strips_what_is_not_translation():
    assert I.normalize("«L’Eco…»") == I.normalize('"L\'Eco..."')


def test_touched_sees_a_changed_word():
    assert I.touched("Craft: Iron", "Crea: Iron") is True


def test_touched_is_not_fooled_by_a_curly_apostrophe():
    """Stessa parola con l'apostrofo tipografico: e' un buco, non una traduzione."""
    assert I.touched("The Sun's Design", "The Sun’s Design") is False


def test_translates_abstains_when_the_other_language_lacks_the_string():
    assert I.translates("The Iron Book", None) is None
    assert I.translates("The Iron Book", "   ") is None


def test_translates_recognises_a_different_rendering():
    assert I.translates("The Iron Book", "Le Livre de Fer") is True


def test_translates_recognises_a_copy():
    assert I.translates("The Iron Book", "The Iron Book") is False


def test_similarity_is_normalised():
    assert I.similarity("abc", "abc") == 1.0
    assert 0.0 <= I.similarity("abc", "xyz") < 0.5
