"""accords.py: gli articoli intorno ai nomi, dopo un rinomino.

Il controllo nasce da un guasto vero e i test lo riproducono: si prende il
dizionario, si rinomina un termine cambiandogli il genere senza toccare gli
articoli - che e' esattamente quello che fa una sostituzione di una riga - e si
verifica che il controllo lo veda. Se un giorno smettesse di vederlo, questi
test cadono prima che cada la traduzione.
"""
import pytest

from conftest import tool

AC = tool("accords")


def test_a_rename_that_changes_gender_is_caught():
    """«Branca Notturna» -> «Ramo Notturno»: il nome e' maschile, gli articoli no."""
    strings = ["il soprintendente della Ramo Notturno", "il motto della Ramo Notturno",
               "la Ramo Notturno intervenne", "il Ramo Notturno fu sciolto"]
    problems = AC.analyze(strings)
    assert any(name.startswith("Ramo") for name, *_ in problems)


def test_the_majority_decides_which_form_is_right():
    strings = ["il Fantoccio Arrossato accetta"] * 5 + ["la Fantoccio Arrossato accetta"]
    (name, best, worst, count, _), = AC.analyze(strings)
    assert name.startswith("Fantoccio")
    assert best[0] == "m" and worst[0] == "f" and count == 1


def test_two_forms_in_balance_are_not_a_finding():
    """Un nome che oscilla a meta' puo' avere due usi: non e' una coda rimasta."""
    strings = ["il Chandler parla"] * 3 + ["la Chandler parla"] * 3
    assert AC.analyze(strings) == []


def test_a_number_difference_is_not_a_finding():
    """«un'Abilita'» e «le Abilita'» convivono: il controllo guarda il genere."""
    strings = ["la Abilita cresce"] * 4 + ["le Abilita crescono"]
    assert AC.analyze(strings) == []


def test_a_verified_discord_is_not_proposed_again():
    strings = ["il Chandler parla"] * 5 + ["la Chandler parla"]
    assert AC.analyze(strings) != []
    assert AC.analyze(strings, known={"Chandler"}) == []


def test_a_missing_elision_is_caught():
    """«il «Imbroglio»» e «della Aula»: davanti a vocale l'articolo si elide."""
    found = AC.elisions(["Democratizza il «Imbroglio»", "Camino della Aula della Divisione"])
    assert len(found) == 2


@pytest.mark.parametrize("text", [
    "lo abbiamo identificato solo il mese dopo",
    "Lui la inseguì per il Bosco",
    "ha avuto l'audacia di pormene uno a sua volta",
])
def test_clitics_are_not_articles(text):
    """Senza questo vincolo il controllo annegava in 115 falsi positivi."""
    assert AC.elisions([text]) == []


def test_a_lowercase_word_is_not_a_game_name():
    """I nomi di gioco portano la maiuscola: le parole comuni non entrano."""
    assert AC.analyze(["la casa era vuota", "il casa era vuoto"] * 3) == []
