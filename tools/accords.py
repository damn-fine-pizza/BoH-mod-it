"""Gli accordi intorno ai nomi di gioco: articoli, preposizioni, elisioni.

Nasce da un guasto vero. Rinominare un termine in tutto il dizionario e' una
sostituzione di una riga - «Branca Notturna» -> «Ramo Notturno» - e sembra
innocua finche' non ci si accorge che il genere e' cambiato: restano dodici
«della Ramo Notturno», un «fu il Ramo stessa», e nessuno degli altri controlli
se ne accorge, perche' il markup e' intatto, i glifi sono giusti, il glossario
e' rispettato e la frase e' grammaticalmente ben formata a livello di parola.

Lo stesso e' successo tre volte nello stesso giro: «Bambola Arrossata» ->
«Fantoccio Arrossato» ha lasciato «la Fantoccio Arrossato»; «Zucca» ->
«Zucchina» ha lasciato «una zucchina propizio»; «Wangle» -> «Imbroglio» ha
lasciato «il «Imbroglio»» senza elisione.

Il controllo prende i nomi che compaiono con l'articolo nel corpus, decide il
genere e il numero dalla forma maggioritaria, e segnala le occorrenze
minoritarie. Non e' un analizzatore grammaticale: e' un contatore che si fida
della maggioranza, ed e' esattamente cio' che serve dopo un rinomino, perche'
la forma sbagliata e' sempre quella rimasta indietro.

Uso: python3 tools/accords.py
"""
import collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

DICT = os.path.join(PROJ, "translations", "it.json")
VERIFIED = os.path.join(PROJ, "translations", "accordi-verificati.json")

# Gli articoli e le preposizioni articolate che precedono un nome, per genere e
# numero. L'apostrofo sta a parte: davanti a vocale l'italiano elide, e la forma
# non elisa e' sempre un errore, non una variante.
DETERMINERS = {
    ("m", "s"): ["il", "lo", "un", "uno", "del", "dello", "al", "allo", "dal", "dallo",
                 "nel", "nello", "sul", "sullo", "quel", "quello", "questo"],
    ("f", "s"): ["la", "una", "della", "alla", "dalla", "nella", "sulla", "quella", "questa"],
    ("m", "p"): ["i", "gli", "dei", "degli", "ai", "agli", "dai", "dagli", "nei", "negli",
                 "sui", "sugli", "quei", "quegli", "questi"],
    ("f", "p"): ["le", "delle", "alle", "dalle", "nelle", "sulle", "quelle", "queste"],
}
OF_DETERMINER = {d: key for key, group in DETERMINERS.items() for d in group}
VOWEL = re.compile(r"^[aeiouAEIOUÀ-ÖØ-öø-ÿ]")
# I nomi si riconoscono dalla maiuscola: sono le carte, le Ore, i luoghi. Le
# parole comuni non entrano, o il controllo annegherebbe nel rumore.
NAME = re.compile(r"\b(" + "|".join(sorted((d for d in OF_DETERMINER), key=len, reverse=True))
                  + r")\s+([A-ZÀ-Ý][\w’'-]{2,}(?:\s+[A-ZÀ-Ý][\w’'-]{2,}){0,2})")


def verified():
    """Le discordanze gia' guardate e volute, con la ragione accanto."""
    try:
        return {k for k in json.load(open(VERIFIED, encoding="utf-8")) if not k.startswith("_")}
    except Exception:
        return set()


def survey(strings):
    """-> {nome: {(genere, numero): quante volte}}"""
    seen = collections.defaultdict(collections.Counter)
    for text in strings:
        for determiner, name in NAME.findall(text):
            seen[name][OF_DETERMINER[determiner]] += 1
    return seen


def analyze(strings, known=frozenset()):
    """-> [(nome, forma buona, forma sbagliata, quante, esempio)]"""
    seen = survey(strings)
    problems = []
    for name, shapes in seen.items():
        if name in known or len(shapes) < 2:
            continue
        (best, most), (worst, fewest) = shapes.most_common()[0], shapes.most_common()[-1]
        # Solo il genere: la differenza di numero e' quasi sempre legittima
        # («un'Abilità» e «le Abilità» convivono benissimo), mentre il genere
        # discorde e' il segno che un rinomino ha lasciato indietro l'articolo.
        if best[0] == worst[0]:
            continue
        # Una sola occorrenza contro molte: e' una coda rimasta indietro.
        # Due forme in equilibrio possono essere due usi diversi dello stesso
        # nome, e non si segnalano: la maggioranza deve essere netta.
        if fewest * 3 > most:
            continue
        sample = next((t for t in strings
                       if re.search(r"\b(" + "|".join(DETERMINERS[worst]) + r")\s+" + re.escape(name), t)), "")
        problems.append((name, best, worst, fewest, sample))
    return sorted(problems, key=lambda p: -p[3])


def elisions(strings):
    """L'articolo non eliso davanti a vocale: «il «Imbroglio»», «della Aula»."""
    # Solo davanti a un nome: una maiuscola, o un caporale che apre una carta.
    # Senza questo vincolo il controllo prende i pronomi clitici - «lo abbiamo
    # identificato», «la inseguì» - che non sono articoli e non si elidono.
    rx = re.compile(r"\b(il|la|lo|una|del|della|dello|al|alla|allo|dal|dalla|dallo"
                    r"|nel|nella|nello|sul|sulla|sullo)\s+([«“][AEIOUÀ-Ý]|[AEIOUÀ-Ý])")
    out = []
    for text in strings:
        for m in rx.finditer(text):
            out.append((m.group(0), text[max(0, m.start() - 30):m.end() + 30]))
    return out


def main():
    strings = list(json.load(open(DICT, encoding="utf-8"))["strings"].values())
    known = verified()
    problems = analyze(strings, known)
    bad_elisions = elisions(strings)
    if not problems and not bad_elisions:
        print(f"{len(strings)} stringhe: articoli e preposizioni in accordo")
        return 0
    if problems:
        print(f"{len(problems)} nomi con l'articolo discorde "
              f"({len(known)} gia' verificati, in accordi-verificati.json)\n")
        for name, best, worst, count, sample in problems:
            def say(shape):
                return ("maschile" if shape[0] == "m" else "femminile") + \
                       (" singolare" if shape[1] == "s" else " plurale")
            print(f"  «{name}»: {say(best)} nel corpus, ma {count} volta/e {say(worst)}")
            print(f"      {sample[:120]}")
    if bad_elisions:
        print(f"\n{len(bad_elisions)} articoli non elisi davanti a vocale\n")
        for form, sample in bad_elisions[:10]:
            print(f"  «{form}» in: {sample[:110]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
