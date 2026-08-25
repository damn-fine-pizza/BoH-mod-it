"""Analisi logica: la resa italiana dice la stessa cosa dell'originale?

Confronta la traduzione con l'inglese su cio' che si puo' contare senza capire
la frase - e che, quando non torna, quasi sempre segnala un pezzo perso o
capovolto. Sono i modi in cui una traduzione lunga sbaglia di senso mentre resta
grammaticalmente perfetta, quindi invisibile a `grammar.py` e a `prose.py`.

 - **i numeri**. «seven years» che diventa «sette anni» e non «sei»: le cifre si
   confrontano come insieme, i numerali scritti attraverso la radice italiana
   (seven -> sett-, che copre sette, settimo, settanta).
 - **la negazione**. Se l'inglese nega e l'italiano no - o il contrario - il
   senso e' rovesciato. E' l'errore piu' grave che una traduzione possa fare, e
   il piu' facile da non vedere rileggendo.
 - **la domanda**. Una frase che finisce con «?» in inglese e con un punto in
   italiano di solito e' una battuta che ha perso il suo tono.
 - **la lunghezza**. Una resa molto piu' corta dell'originale ha perso una
   proposizione; molto piu' lunga, ne ha aggiunta una.
 - **le coppie di segni**: parentesi, quadre, caporali e virgolette alte devono
   chiudersi.

Ogni sonda e' un indizio, non una condanna: si legge l'elenco.

Uso:
    python3 tools/logic.py            l'elenco per tipo
    python3 tools/logic.py -v         tutte le occorrenze
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

DICT = os.path.join(PROJ, "translations", "it.json")
VERIFIED = os.path.join(PROJ, "translations", "logica-verificate.json")

NUMERALS = {
    "one": "un", "two": "due", "three": "tre", "four": "quattr", "five": "cinqu",
    "six": "sei", "seven": "sett", "eight": "ott", "nine": "nov", "ten": "dieci",
    "eleven": "undic", "twelve": "dodic", "thirteen": "tredic", "twenty": "vent",
    "thirty": "trent", "forty": "quarant", "fifty": "cinquant", "hundred": "cent",
    "thousand": "mil", "first": "prim", "second": "second", "third": "terz",
    "fourth": "quart", "fifth": "quint", "sixth": "sest", "seventh": "settim",
}
NEG_EN = re.compile(r"\b(not|never|no|none|nothing|nobody|neither|nor|without|"
                     r"cannot|can't|won't|don't|doesn't|didn't|isn't|aren't|wasn't|"
                     r"weren't|shouldn't|wouldn't|couldn't|hasn't|haven't)\b", re.I)
NEG_IT = re.compile(r"\b(no|non|mai|nessun\w*|niente|nulla|né|senza|neppure|nemmeno|"
                     r"neanche|fuori|privo\w*|priva\w*)\b", re.I)
PAIRS = [("(", ")"), ("[", "]"), ("«", "»"), ("“", "”")]

# le cifre che l'italiano scrive in lettere: «1st Baron» -> «Primo Barone»
DIGIT_WORD = {"1": ("prim", "un", "uno", "una"), "2": ("second", "due"),
                "3": ("terz", "tre"), "4": ("quart", "quattro"), "5": ("quint", "cinque"),
                "6": ("sest", "sei"), "7": ("settim", "sette"), "8": ("ottav", "otto"),
                "9": ("non", "nove"), "10": ("decim", "dieci"), "11": ("undic", "XI"),
                "12": ("dodic", "XII"), "13": ("tredic", "XIII"), "14": ("quattordic", "XIV"),
                "15": ("quindic", "XV"), "16": ("sedic", "XVI"), "18": ("diciott", "XVIII")}


def quotation_marks(t):
    """Quanti apici, nell'inglese, aprono o chiudono una citazione.

    Non si contano i genitivi sassoni (Yvette's, Ys') ne' le contrazioni
    (don't), che usano lo stesso segno. Serve perche' l'originale e' spesso
    sbilanciato apposta - le citazioni lunghe dei tomi sono spezzate in piu'
    xext e ogni pezzo ne porta un capo solo - e segnalare quello come difetto
    italiano dava 36 segnalazioni su 36 sbagliate."""
    t = re.sub(r"(?<=[A-Za-z])['\u2019](?=[a-z])", "", t)      # don't, isn't
    t = re.sub(r"(?<=[A-Za-z])['\u2019](?=s\b)", "", t)        # Yvette's
    t = re.sub(r"(?<=s)['\u2019](?=\s|$)", "", t)              # Ys'
    return len(re.findall(r"['\u2018\u2019\u201c\u201d]", t))


def clean(t):
    t = re.sub(r"<[^<>\n]{1,40}>", "", t)
    t = re.sub(r"\{[A-Z]+:[^}]*\}", "", t)
    return t


def digits(t):
    return collections.Counter(re.findall(r"\d+", t))


def main():
    verbose = "-v" in sys.argv
    s = json.load(open(DICT, encoding="utf-8"))["strings"]
    try:
        with open(VERIFIED, encoding="utf-8") as f:
            seen = {k for k in json.load(f) if not k.startswith("_")}
    except FileNotFoundError:
        seen = set()
    prob = collections.defaultdict(list)
    for en, it in s.items():
        if en in seen:
            continue
        e, i = clean(en), clean(it)
        el, il = e.lower(), i.lower()

        # 1. cifre; una cifra scritta in lettere in italiano non e' un errore
        ce, ci = digits(e), digits(i)
        if ce != ci:
            # i secoli: l'inglese scrive «the 16th century», l'italiano «il XVI
            # secolo», e il numero arabo sparisce per forza
            # l'italiano dice i secoli e i decenni a modo suo: «il XVI secolo»,
            # «nell'Ottocento», «gli anni Venti». Il numero arabo sparisce, e
            # non e' un pezzo perso.
            roman_numerals = bool(re.search(r"\b[IVXLCDM]{1,7}\b|Ottocento|Novecento|Settecento|"
                                    r"Seicento|Cinquecento|Quattrocento|anni\s+[A-Z]", i))
            missing = [n for n in (ce - ci).elements()
                        if not any(r in il for r in DIGIT_WORD.get(n, ()))
                        and not (roman_numerals and re.search(r"%s(?:s|st|nd|rd|th)\b" % n, e))]
            added = list((ci - ce).elements())
            if missing or added:
                prob["numeri diversi fra originale e resa"].append(
                    (f"EN {sorted(ce.elements())} IT {sorted(ci.elements())}", en, it))

        # 2. numerali scritti
        for word, root in NUMERALS.items():
            if word in ("one", "second", "third", "first"):
                continue          # in inglese sono anche pronomi e avverbi
            if re.search(r"\b%s\b" % word, el) and root not in il:
                prob["numerale scritto non ritrovato nella resa"].append(
                    (f"{word} -> {root}…", en, it))
                break

        # 3. negazione: solo il verso che rovescia il senso, e solo quando
        # l'inglese nega piu' di una volta senza che l'italiano neghi mai.
        # L'altro verso e' quasi sempre l'italiano che rende «unauthorised» con
        # «non autorizzata», e dava 327 segnalazioni sbagliate.
        ne = len(NEG_EN.findall(e))
        if ne >= 2 and not NEG_IT.search(i):
            prob["negazione: l'inglese nega e l'italiano no"].append(
                (f"{ne} negazioni nell'originale", en, it))

        # 4. domanda; via le virgolette di chiusura, o «skies?'» non risulta
        # una domanda e «cieli»?» si'
        final = lambda t: t.rstrip().rstrip("'’\"”»)]").rstrip().endswith("?")
        if final(e) != final(i):
            prob["punto interrogativo solo da una parte"].append(("", en, it))

        # 5. lunghezza
        pe, pi = len(e.split()), len(i.split())
        if pe >= 20 and (pi / pe < 0.55 or pi / pe > 1.9):
            prob["lunghezza sproporzionata (pezzo perso o aggiunto?)"].append(
                (f"EN {pe} parole, IT {pi}", en, it))

        # 6. coppie di segni; il metro e' l'originale, che e' spesso irregolare
        for a, b in PAIRS:
            offset = i.count(a) - i.count(b)
            if offset == 0:
                continue
            if (a, b) in (("«", "»"), ("“", "”")):
                # un numero dispari di apici nell'originale vuol dire citazione
                # spezzata: uno scarto di uno e' quello che deve essere
                if abs(offset) == 1 and quotation_marks(e) % 2 == 1:
                    continue
            elif offset == e.count(a) - e.count(b):
                continue                      # sbilanciato come l'inglese
            prob[f"segni non chiusi: {a} {b}"].append(
                (f"{i.count(a)}{a} contro {i.count(b)}{b}", en, it))

    tot = sum(len(v) for v in prob.values())
    print(f"{len(s)} stringhe confrontate con l'originale"
          f" ({len(seen)} gia' verificate, in {os.path.basename(VERIFIED)})\n")
    if not tot:
        print("nessuna incongruenza")
        return 0
    print(f"{tot} segnalazioni\n")
    for name, cases in sorted(prob.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name}: {len(cases)}")
        for note, en, it in cases[: (300 if verbose else 3)]:
            if note:
                print(f"      {note}")
            print(f"      EN {en[:150]!r}")
            print(f"      IT {it[:150]!r}")
        if not verbose and len(cases) > 3:
            print(f"      ... e altri {len(cases)-3} (-v per vederli)")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
