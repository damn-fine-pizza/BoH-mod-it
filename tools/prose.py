"""Ortotipografia della prosa: quello che style.py fa sulle UI label, ma sul testo.

style.py, style2.py e style3.py guardano le 295 label dell'interfaccia. Le
276.000 parole di prosa non avevano niente, e infatti ci e' rimasta dentro
l'ortotipografia inglese: il trattino breve al posto della lineetta, i doppi
spazi, le virgolette annidate rese con altri caporali.

Il metro sono le due localizzazioni di riferimento (bohloc.ES, bohloc.FR)
lette insieme all'originale, ma la decisione finale e' la norma italiana:
dove francese e spagnolo divergono, il conteggio dice solo dove guardare.

    python3 tools/prose.py              misura e mostra gli esempi
    python3 tools/prose.py --apply    riscrive translations/it.json
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

DICT = os.path.join(PROJ, "translations", "it.json")

# --- R1. la lineetta parentetica ------------------------------------------
# L'inglese scrive " - ", un trattino breve fra due spazi. E' la resa ASCII
# della spaced en dash britannica: Kennedy e' inglese e l'inglese britannico
# vuole " – ", non l'em dash chiuso all'americana.
# L'italiano non usa il trattino come lineetta in nessun caso: la lineetta
# parentetica e' – (trattino medio) fra due spazi.
# Misura sui tre corpora, per stringhe che contengono almeno un'occorrenza:
#                    " - "    "—"
#   inglese (core)    1304      2
#   francese          1249      1     <- ha ricopiato l'inglese
#   spagnolo            27    540     <- ha applicato la raya
# Lo spagnolo pero' non e' un modello sulla spaziatura: la RAE incolla la
# raya al testo racchiuso (405 aperture " —x", 233 chiusure "x— "), che
# l'italiano non fa. Del modello spagnolo si prende solo "non e' un trattino".
DASH = "–"

# " - " fra due caratteri qualunque, tranne fra due cifre (intervalli: 1451-1551,
# che comunque non hanno spazi) e tranne le eccezioni elencate qui sotto.
_PARENTHETICAL      = re.compile(r"(?<=\S) - (?=\S)")
_SUSPENDED_END = re.compile(r"(?<=\S) -(?=[\s»\"']|$)")     # frase interrotta: "Oh, cielo -»"
_SUSPENDED_START = re.compile(r"(?m)^([ \t]*)-(?= )")          # a inizio riga: "- incrinato -"
_EMDASH      = re.compile(r"(?<=\S) — (?=\S)")       # i due casi gia' a em dash

# Il '-' che non e' una lineetta ma il nome di un tasto.
DASH_EXEMPT = {
    "Space pauses; numpad + and - change speed up and down; "
    "you can change these keyboard shortcuts in Settings.",
}

# --- R2. il doppio spazio --------------------------------------------------
# Ricopiato dall'inglese, che ne ha 199. La chiave inglese non si tocca:
# e' l'indice del dizionario e deve restare identica al core.
_DOUBLE = re.compile(r"(?<=\S)[ ]{2,}(?=\S)")

# --- R3. le virgolette di secondo livello ----------------------------------
# L'inglese ha un livello solo, '…', e lo annida dentro se stesso. L'italiano
# apre con i caporali e per il secondo livello usa le virgolette alte “…”.
# Nel dizionario convivono le due rese: 60 occorrenze annidate corrette con “…”
# e 45 stringhe con caporali dentro caporali. Nessuna “ compare a primo livello,
# quindi la direzione della correzione non e' ambigua.
def _nested(v):
    """Riscrive le coppie di caporali di secondo livello come “…”."""
    out = list(v)
    stack = []
    for i, c in enumerate(v):
        if c == "«":
            stack.append(i)
        elif c == "»" and stack:
            opener = stack.pop()
            if stack:                       # eravamo gia' dentro un caporale
                out[opener] = "“"
                out[i] = "”"
    # un'apertura di secondo livello rimasta senza chiusura (la battuta prosegue
    # in un'altra stringa) va comunque abbassata di livello
    if len(stack) > 1:
        for opener in stack[1:]:
            out[opener] = "“"
    return "".join(out)


RULES = []

def rule(name, explain):
    def deco(f):
        RULES.append((name, explain, f))
        return f
    return deco


@rule("lineetta parentetica", "trattino breve al posto di –")
def r_dash(en, it):
    if en in DASH_EXEMPT:
        return it
    it = _PARENTHETICAL.sub(f" {DASH} ", it)
    it = _SUSPENDED_END.sub(f" {DASH}", it)
    it = _SUSPENDED_START.sub(rf"\1{DASH}", it)
    it = _EMDASH.sub(f" {DASH} ", it)
    return it


@rule("doppio spazio", "spaziatura ricopiata dall'inglese")
def r_double(en, it):
    return _DOUBLE.sub(" ", it)


@rule("caporali annidati", "secondo livello: “…”, non «…»")
def r_nested(en, it):
    return _nested(it) if it.count("«") > 1 else it


def review(pairs):
    """-> {regola: [(en, prima, dopo)]}"""
    found = collections.defaultdict(list)
    for en, it in pairs:
        for name, _, f in RULES:
            fresh_one = f(en, it)
            if fresh_one != it:
                found[name].append((en, it, fresh_one))
                it = fresh_one
    return found


def apply_fixes(strings):
    n = 0
    for en, it in list(strings.items()):
        fresh_one = it
        for _, _, f in RULES:
            fresh_one = f(en, fresh_one)
        if fresh_one != it:
            strings[en] = fresh_one
            n += 1
    return n


def main():
    d = json.load(open(DICT, encoding="utf-8"))
    if "--apply" in sys.argv:
        n = apply_fixes(d["strings"])
        json.dump(d, open(DICT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print(f"{n} stringhe riscritte")
        return 0
    found = review(d["strings"].items())
    if not found:
        print(f"{len(d['strings'])} stringhe: ortotipografia della prosa a posto")
        return 0
    how_many = 4
    for name, explain, _ in RULES:
        cases = found.get(name)
        if not cases:
            continue
        print(f"  {name} ({explain}): {len(cases)} stringhe")
        for en, before, after in cases[:how_many]:
            print(f"      -  {before[:110]!r}")
            print(f"      +  {after[:110]!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
