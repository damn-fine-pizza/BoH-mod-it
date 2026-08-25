"""Analisi grammaticale della resa italiana: accordi, elisioni, refusi di forma.

Non e' un correttore ortografico - non ne serviva uno, il testo e' scritto bene -
ma un insieme di sonde per gli errori che una traduzione fatta a pezzi produce e
che rileggere non prende, perche' sono minuscoli e stanno in mezzo a 276.000
parole. Ognuna e' deterministica: o la regola c'e' o non c'e'.

Che cosa cerca, e perche':

 - **genere sbagliato dell'articolo**. «il conflagrazione» era li' da un giro
   intero. I suffissi italiani dicono il genere senza ambiguita': -zione, -sione,
   -tudine, -tu', -ta' sono femminili; -mento, -aggio, -ore sono maschili. Se
   l'articolo che precede e' dell'altro genere, e' un errore.
 - **elisione e preposizioni articolate**. «all'Spuntare», che e' nato da una
   sostituzione in blocco fatta qui dentro; «un'uomo» con l'apostrofo davanti a
   un maschile; «un ora» senza.
 - **l'articolo davanti a s impura, gn, ps, z**: «il stesso», «un scudo».
 - **accenti**: perche', poiche', se', un po', qual e'.
 - **parola ripetuta**: «la la», «che che».
 - **spazio prima della punteggiatura**, e virgola prima di una chiusa.

Uso:
    python3 tools/grammar.py            l'elenco per tipo
    python3 tools/grammar.py -v         tutte le occorrenze, non le prime tre
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

DICT = os.path.join(PROJ, "translations", "it.json")

MASCULINE_WORDS = ("il", "lo", "un", "uno", "del", "dello", "al", "allo", "dal", "dallo",
            "nel", "nello", "sul", "sullo", "questo", "quello", "quel")
FEMININE = ("la", "una", "della", "alla", "dalla", "nella", "sulla", "questa", "quella")

# suffissi che fissano il genere senza eccezioni utili in questo corpus
SUFF_F = ("zione", "sione", "gione", "tudine", "itudine", "ezza", "izia", "enza", "anza")
SUFF_M = ("mento", "aggio")

# parole che finiscono in -ore ma sono femminili, o in -zione ma non nomi
EXCEPTIONS = {"folgore", "moglie", "abbastanza", "senza", "danza", "stanza", "usanza"}
# parole italiane che finiscono in -che' col grave e sono corrette
GRAVE_OK = {"lacchè", "caffè", "tè", "canapè", "narghilè", "gilè"}

RULES = [
    ("genere: articolo maschile + nome femminile",
     re.compile(r"\b(%s)\s+([^\W\d_]+(?:%s))\b" % ("|".join(MASCULINE_WORDS), "|".join(SUFF_F)), re.I)),
    ("genere: articolo femminile + nome maschile",
     re.compile(r"\b(%s)\s+([^\W\d_]+(?:%s))\b" % ("|".join(FEMININE), "|".join(SUFF_M)), re.I)),
    # i numeri romani restano fuori: «dall'XI secolo» si legge «dall'undicesimo»
    ("elisione: apostrofo davanti a consonante",
     re.compile(r"\b(?:l|un|dell|all|dall|nell|sull|quest|quell)['’]"
                r"(?![IVXLCDM]+\b)(?=[bcdfgjklmnpqrstvwz])", re.I)),
    ("elisione: un' davanti a maschile",
     re.compile(r"\bun['’](?=(?:uomo|anno|altro\b|amico|attimo|istante|angolo|occhio|orecchio)\b)", re.I)),
    # solo "una": "lo"/"la" davanti a vocale sono quasi sempre pronomi
    # ("lo abbiamo identificato"), e non si elidono
    ("elisione: una davanti a vocale",
     re.compile(r"\buna\s+(?=[aeiouàèéìòù])[^\W\d_]{3,}", re.I)),
    # i numeri romani restano fuori: «il XVI secolo» e' corretto
    ("s impura, gn, ps, z: vuole lo/uno",
     re.compile(r"\b(?:il|un)\s+(?!(?:[IVXLCDM]+)\b)(?:s[bcdfgklmnpqrtvz]|gn|ps|pn|x|z)[^\W\d_]+")),
    ("accento: -che' vuole l'accento acuto, non il grave",
     re.compile(r"\b\w*chè\b", re.I)),
    ("accento: se' pronome, un po', qual e'",
     re.compile(r"\bsè\b|\bun\s+po(?![’'])\b|\bun\s+pò\b|\bqual['’]\s*è\b", re.I)),
    # Solo le parole funzionali. L'italiano raddoppia apposta gli aggettivi e le
    # onomatopee - «piccolo piccolo», «Pip pip», «Hee hee» - ed erano 24
    # segnalazioni su 27, tutte legittime; un articolo o una preposizione
    # ripetuti sono invece sempre un errore di copia.
    ("parola funzionale ripetuta",
     re.compile(r"\b(il|lo|la|i|gli|le|un|una|del|della|dei|delle|di|da|in|con|su|per|"
                r"tra|fra|che|chi|cui|non|si|ma|se|come|quando|dove|perché|al|alla|ai|"
                r"alle|dal|dalla|nel|nella|sul|sulla|è|hai|hanno|sono|era)\s+\1\b")),
    # «ha ha» e «ho ho» sono risate, non ausiliari ripetuti, e restano fuori;
    # il confronto e' sensibile alle maiuscole, cosi' «di DI Douglas Moore» -
    # dove DI e' Detective Inspector - non e' una ripetizione.
    # il segnaposto \x00 sta dove c'era un tag: «Interesse per <sprite>.» non e'
    # uno spazio prima del punto, e senza questa esclusione erano 447 su 481
    # I verbi che in italiano esistono solo pronominali: «trust» reso «fidare»
    # transitivo («non mi fidano» per «I am not trusted») e' l'errore tipico di
    # una traduzione fatta a pezzi, e nessun'altra sonda lo prende. La forma
    # giusta e' «non si fidano di me».
    # «mi fido» e' corretto (io mi fido); «non mi fidano» no, perche' il verbo e'
    # alla terza persona e il pronome alla prima: vuol dire «essi fidano me», che
    # in italiano non si dice. Il criterio e' quindi la discordanza di persona,
    # non il verbo in se'.
    ("verbo pronominale usato come transitivo",
     re.compile(r"\b(mi|ti|ci|vi)\s+"
                r"(?:fid|pent|vergogn|arrend|accorg|impadron)"
                r"(?:a|ano|ava|avano|erà|eranno|ò|arono|ino|asse|assero)\b", re.I)),
    ("spazio prima della punteggiatura",
     re.compile(r"[^\s\x00]\s+[,;:.!?](?!\.)")),
]

# le forme corrette che le regole sugli accenti prenderebbero comunque
ACUTE_OK = re.compile(r"\b(?:perché|poiché|affinché|benché|nonché|sicché|giacché|"
                           r"purché|cosicché|finché|anziché|granché|macché|ché)\b")


def strings():
    d = json.load(open(DICT, encoding="utf-8"))
    return d["strings"]


def clean(t):
    """Via i tag e i template: dentro non c'e' italiano da controllare.

    Si tolgono senza lasciare spazio al loro posto, o la sonda sullo spazio
    prima della punteggiatura segnalerebbe ogni «<i>parola</i>.» del corpus."""
    t = re.sub(r"<[^<>\n]{1,40}>", "\x00", t)
    t = re.sub(r"\{[A-Z]+:[^}]*\}", "\x00", t)
    t = re.sub(r"@#[^@]*@", "\x00", t)
    return t


def main():
    verbose = "-v" in sys.argv
    s = strings()
    found = collections.defaultdict(list)
    for en, it in s.items():
        text = clean(it)
        for name, rx in RULES:
            for m in rx.finditer(text):
                fragment = m.group(0)
                # se l'originale inglese ha lo stesso tratto, non e' un difetto
                # nostro: «Opportunity: ?» diventa «Occasione: ?» e lo spazio
                # prima del punto interrogativo c'era gia'
                if name.startswith("spazio prima") and re.search(
                        r"[^\s]\s+[,;:.!?]", clean(en)):
                    continue
                if name.startswith("accento: -che") and fragment.lower() in GRAVE_OK:
                    continue
                if name.startswith("genere") and any(x in fragment.lower() for x in EXCEPTIONS):
                    continue
                if name.startswith("spazio prima") and fragment[-1] == "." and "…" in fragment:
                    continue
                start = max(0, m.start() - 40)
                found[name].append((fragment, text[start:m.end() + 40], en))
    tot = sum(len(v) for v in found.values())
    print(f"{len(s)} stringhe esaminate\n")
    if not tot:
        print("nessuna segnalazione grammaticale")
        return 0
    print(f"{tot} segnalazioni\n")
    for name, cases in sorted(found.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name}: {len(cases)}")
        for fragment, context, en in cases[: (200 if verbose else 3)]:
            print(f"      {fragment!r}")
            print(f"        …{context.strip()}…")
        if not verbose and len(cases) > 3:
            print(f"      ... e altri {len(cases)-3} (-v per vederli)")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
