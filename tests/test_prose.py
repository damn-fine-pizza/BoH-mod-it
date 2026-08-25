"""L'ortotipografia della prosa: le tre regole di prose.py.

Sono correzioni che riscrivono il dizionario, quindi vanno sapute a memoria:
una regola troppo larga rovina il testo di 12.677 stringhe in un colpo solo, e
il danno si vede solo giocando.
"""
from conftest import tool

p = tool("prose")


def test_the_parenthetical_dash_becomes_an_en_dash():
    assert p.r_dash("x - y", "il tempo - quello vero - passa") == "il tempo – quello vero – passa"


def test_the_suspended_dash_at_the_end_of_a_sentence():
    assert p.r_dash("", "Oh, cielo -»") == "Oh, cielo –»"


def test_the_dash_at_the_start_of_a_line():
    assert p.r_dash("", "- incrinato") == "– incrinato"


def test_an_existing_em_dash_becomes_the_italian_dash():
    assert p.r_dash("", "il tempo — quello vero") == "il tempo – quello vero"


def test_numeric_ranges_are_not_dashes():
    """1451-1551 non ha spazi: la regola non deve vederlo."""
    assert p.r_dash("", "La Guerra delle Strade, 1451-1551") == "La Guerra delle Strade, 1451-1551"


def test_the_minus_key_is_not_a_dash():
    """L'unica stringa esente: «numpad + and -» parla di una tastiera."""
    exempt = next(iter(p.DASH_EXEMPT))
    assert p.r_dash(exempt, exempt) == exempt


def test_the_double_space_copied_from_english_goes():
    assert p.r_double("a  b", "il  cielo") == "il cielo"


def test_leading_indentation_survives():
    """Serve solo fra due parole: l'indentazione dei tomi non si tocca."""
    assert p.r_double("", "  indentato") == "  indentato"


def test_second_level_guillemets_become_curly_quotes():
    assert p.r_nested("", "«disse «no» e usci'»") == "«disse “no” e usci'»"


def test_a_single_guillemet_pair_is_left_alone():
    assert p.r_nested("", "«una battuta sola»") == "«una battuta sola»"


def test_an_unclosed_second_level_is_lowered_anyway():
    """La battuta prosegue in un'altra stringa: il livello va abbassato comunque."""
    assert p.r_nested("", "«disse «no").count("“") == 1


def test_review_reports_which_rule_touched_what():
    found = p.review([("x - y", "il tempo - quello vero")])
    assert "lineetta parentetica" in found
    en, before, after = found["lineetta parentetica"][0]
    assert before == "il tempo - quello vero" and after == "il tempo – quello vero"


def test_apply_fixes_rewrites_and_counts():
    strings = {"a - b": "il tempo - quello vero", "ok": "niente da fare"}
    n = p.apply_fixes(strings)
    assert n == 1 and strings["a - b"] == "il tempo – quello vero"
    assert strings["ok"] == "niente da fare"


def test_apply_fixes_is_idempotent():
    """Rilanciarlo non deve continuare a cambiare le stesse stringhe."""
    strings = {"a - b": "il tempo - quello vero"}
    p.apply_fixes(strings)
    assert p.apply_fixes(strings) == 0
