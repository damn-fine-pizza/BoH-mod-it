"""validate.py e gli altri controlli che leggono il dizionario.

validate.analyze e' il gate piu' severo: markup, glossario, nomi propri,
regola del neutro, ortotipografia, glifi. Qui gli si passano regole finte, cosi'
i casi restano leggibili e i test non dipendono dal glossario vero, che cambia.
"""
import re

import pytest

from conftest import tool

V = tool("validate")
TE = tool("terms")
CO = tool("consistency")
CX = tool("context")

# (constraints, never, atlas, exceptions, forbidden, exempt)
ATLAS = {ord(c) for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ "
                           "àèéìòùÀÈÉÌÒÙ’«»“”–…!?.,;:'\"<>/{}[]$0123456789-\n"}
RULES = ({"Lantern": "Lanterna"}, {"Ereb"}, ATLAS, {}, [], set())


def check_pair(en, it, rules=RULES):
    return V.analyze([(en, it)], rules)


def test_a_clean_pair_reports_nothing():
    assert check_pair("The Lantern burns", "La Lanterna brucia") == {}


def test_the_glossary_is_binding():
    prob = check_pair("The Lantern burns", "Il Faro brucia")
    assert "glossario: Lantern -> Lanterna" in prob


def test_never_translate_terms_must_survive():
    assert "non tradurre: Ereb" in check_pair("Ereb waits", "Attende")


def test_known_limit_the_term_is_matched_as_a_substring():
    """«Erebo» contiene «Ereb», quindi passa: il controllo sull'inglese usa i
    confini di parola, quello sull'italiano no. Se un giorno si vuole prendere
    anche questo caso, questo test e' il posto dove accorgersene."""
    assert check_pair("Ereb waits", "Erebo attende") == {}


def test_altered_tags_are_caught():
    assert "tag alterati" in check_pair("<i>x</i>", "y")


def test_game_tokens_are_untouchable():
    assert "token {SETTING} alterati" in check_pair("{SPHERE:a}", "{SPHERE:b}")


def test_newlines_are_counted():
    assert "a-capo" in check_pair("a\nb", "a b")


def test_the_gender_neutral_rule():
    """Il gioco non dichiara il genere di chi lo gioca: la prima persona non lo fissa."""
    prob = check_pair("I arrived", "Sono arrivato")
    assert "genere fissato (regola del neutro)" in prob


def test_the_neutral_rule_can_be_waived_per_string():
    """Vale per l'Archivista, non per i visitatori che parlano di se'."""
    rules = (RULES[0], RULES[1], RULES[2], {}, [], {"I arrived"})
    assert check_pair("I arrived", "Sono arrivato", rules) == {}


def test_an_epicene_adjective_is_not_a_gendered_form():
    """«felice» vale per chiunque. Segnalarlo spingeva a scrivere «provo
    felicita'», che dice un'altra cosa: un controllo che fa scrivere peggio e'
    un controllo rotto (convenzioni 5-quaterdecies)."""
    assert check_pair("and I am happy", "e sono felice") == {}


def test_an_invariable_locution_is_not_a_predicative_adjective():
    """«al sicuro» non concorda con nessuno. «sicuro» da solo si'."""
    assert check_pair("I am safe", "sono al sicuro") == {}
    assert "genere fissato (regola del neutro)" in check_pair("I am sure", "sono sicuro")


def test_an_adverb_between_the_verb_and_the_adjective_is_still_caught():
    """Restringere a un avverbio non deve aprire un buco: la preposizione e'
    esclusa, l'avverbio no."""
    assert "genere fissato (regola del neutro)" in check_pair("I'm ready", "sono già pronto")


def test_the_deliberate_masculine_is_a_registry_not_a_silence(tmp_path, monkeypatch):
    """Il maschile non marcato e' ammesso dove il neutro costa la frase, ma
    riga per riga e con la ragione accanto: `archivista_al_maschile` entra
    nelle esenzioni esattamente come `neutro_non_si_applica`."""
    import json
    finto = tmp_path / "glossario.json"
    finto.write_text(json.dumps({
        "principi": {}, "sapienze": {}, "ruoli_e_luoghi": {}, "ricorrenti": {},
        "mai_tradurre": [],
        "neutro_non_si_applica": {"I was afraid": "parla Azita, l'inglese la chiama «her»."},
        "archivista_al_maschile": {"I'm ready": "«Tutto pronto» descrive gli attrezzi, non chi li usa."},
    }, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(V, "GLOSSARY", str(finto))
    exempt = V.load_rules()[5]
    assert "I'm ready" in exempt and "I was afraid" in exempt
    assert V.analyze([("I'm ready", "Sono pronto")], V.load_rules()) == {}


def test_a_straight_apostrophe_is_an_error():
    assert "virgolette o apostrofo dritti" in check_pair("the soul's", "l'anima")


def test_glyphs_outside_the_atlas_are_caught():
    """Un carattere che il font del gioco non ha esce come rettangolo vuoto."""
    prob = check_pair("x", "x字")
    assert any(k.startswith("glifi fuori atlante") for k in prob)


def test_a_term_can_be_exempted_string_by_string():
    rules = ({"Lantern": "Lanterna"}, set(), ATLAS, {"Lantern": {"Sea's Lantern"}}, [], set())
    assert check_pair("Sea's Lantern", "Sea’s Lantern", rules) == {}


# --- terms ---------------------------------------------------------------

def test_roots_keep_the_first_sixty_percent():
    assert TE.roots("Il Libro di Ferro") == ["libr", "ferr"]


def test_use_label_recognises_an_inflected_card():
    assert TE.use_label("parla dei Libri di Ferro", "Libro di Ferro") is True


def test_use_label_says_no_when_the_card_is_absent():
    assert TE.use_label("parla di tutt'altro", "Libro di Ferro") is False


# --- consistency ---------------------------------------------------------

def test_clean_strips_markup_before_terms_are_sought():
    assert "The Iron" in CO.clean("<i>The Iron</i> {ASPECT:x} Book")


def test_terms_never_start_with_a_function_word():
    """«The Iron Book» comincia con The: il termine e' quello che segue, non la frase."""
    assert CO.terms_of("He read The Iron Book at Hush House") == {"Hush House"}


# --- context -------------------------------------------------------------

def test_shape_tells_label_from_sentence_from_prose():
    assert CX.shape("Il Libro") == 0
    assert CX.shape("x" * 100) == 1
    assert CX.shape("x" * 200) == 2


def test_show_escapes_newlines_instead_of_printing_them():
    """Chi traduce deve contarli: se si stampano davvero, spariscono dal formato."""
    assert CX.show("a\nb") == "a\\nb"
