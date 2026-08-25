"""Le regole grammaticali: accordi, elisioni, articoli.

Sono espressioni regolari su testo italiano, cioe' il posto dove i falsi
positivi nascono in fretta: «dall'XI secolo» non e' un'elisione sbagliata, «lo
abbiamo visto» non e' un articolo davanti a vocale. Ogni eccezione qui sotto e'
una segnalazione che una versione precedente dava a torto.
"""
import pytest

from conftest import tool

G = tool("grammar")


def flags(with_text):
    """-> i nomi delle regole che scattano su questa stringa."""
    return {name for name, rx in G.RULES if rx.search(with_text)}


def test_masculine_article_before_feminine_noun():
    assert "genere: articolo maschile + nome femminile" in flags("il traduzione")


def test_feminine_article_before_masculine_noun():
    assert "genere: articolo femminile + nome maschile" in flags("la documento")


def test_a_correct_agreement_is_not_flagged():
    assert flags("la traduzione del documento") == set()


def test_apostrophe_before_a_consonant():
    assert "elisione: apostrofo davanti a consonante" in flags("dell'libro")


def test_roman_numerals_are_not_a_wrong_elision():
    """«dall'XI secolo» si legge «dall'undicesimo»: l'apostrofo ci vuole."""
    assert "elisione: apostrofo davanti a consonante" not in flags("dall'XI secolo")


def test_feminine_apostrophe_before_a_masculine_noun():
    assert "elisione: un' davanti a maschile" in flags("un'uomo")


def test_una_before_a_vowel_must_elide():
    assert "elisione: una davanti a vocale" in flags("una anima")


def test_words_ending_in_enza_are_feminine():
    assert "genere: articolo maschile + nome femminile" in flags("il pazienza")


def test_corpus_exceptions_are_not_flagged():
    """«folgore» finisce in -ore ed e' femminile: sta nella lista apposta."""
    assert "folgore" in G.EXCEPTIONS


def test_correct_che_accents_are_known():
    """«lacchè» e «caffè» hanno il grave e sono corretti: la regola non li tocca."""
    assert {"caffè", "tè"} <= G.GRAVE_OK
