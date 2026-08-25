"""Un termine inglese, una resa italiana: trova quelli che ne hanno due o tre.

`validate.py` tiene ferme le rese che qualcuno ha gia' deciso e scritto nel
glossario; `terms.py` controlla che la prosa chiami le carte come si chiamano.
Resta scoperto tutto cio' che non e' ne' l'uno ne' l'altro: i nomi che compaiono
solo nella prosa. «Omar, the Blaze» era diventato *la Vampa* due volte, *il
Bagliore* una e *il Vampo* una, e nessuno dei due strumenti poteva accorgersene,
perche' non e' una carta e nessuno l'aveva messo nel glossario.

Come funziona. Si prendono i termini dell'originale che sembrano nomi - una o
piu' parole maiuscole, mai a inizio frase - e che ricorrono almeno tre volte.
Per ciascuno si guarda che cosa c'e' nelle rese italiane: se il termine e'
rimasto invariato, o quale gruppo di parole maiuscole compare al suo posto.

Il punto delicato e' scegliere il candidato giusto fra i gruppi maiuscoli della
stessa frase, che sono tanti. Non basta contarli: «Archivista» compare accanto a
tutto, e la prima versione dava 696 termini divergenti, quasi tutti sbagliati.
Serve l'associazione: un gruppo e' la resa di un termine se compare quasi solo
dove c'e' quel termine (qui: almeno i due terzi delle sue occorrenze totali).
Cosi' «Vampa» resta candidato di «Blaze», mentre «Archivista» non e' candidato
di niente, perche' sta ovunque.

Non basta ancora: «Mistero», «Interesse» e «Prova» stanno quasi sempre nella
stessa frase - «[Prova un libro con tanto Mistero quanto il loro Interesse]» -
e ognuno risultava candidato degli altri due. Quindi ogni gruppo italiano viene
assegnato a un solo termine inglese, quello con cui ricorre piu' spesso, e
compare fra i candidati solo di quello.

E infine: due rese sono varianti l'una dell'altra solo se si escludono. Dove c'e'
«la Vampa» non c'e' «il Bagliore»; «Radici» e «Riti» invece stanno nella stessa
frase - «Riti delle Radici» - e non sono affatto due modi di dire la stessa cosa.
Si chiede quindi che le stringhe dei due candidati si sovrappongano poco.

E' una sonda statistica, non una prova: si legge l'elenco e si decide. La forma
giusta e' quella della carta se la carta esiste, altrimenti la maggioranza.

Uso:
    python3 tools/consistency.py            le divergenze, dalla piu' frequente
    python3 tools/consistency.py --min 5    solo i termini che ricorrono almeno 5 volte
    python3 tools/consistency.py -v         con tutte le stringhe
"""
import json, os, re, sys, collections, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

DICT = os.path.join(PROJ, "translations", "it.json")
GLOSSARY = os.path.join(PROJ, "translations", "glossario.json")
VERIFIED = os.path.join(PROJ, "translations", "coerenza-verificate.json")

# parole inglesi maiuscole che non sono nomi: aprono frase o sono di servizio
FUNCTION_WORDS = {"The", "A", "An", "I", "In", "It", "If", "But", "And", "Or", "Of", "To",
            "That", "This", "There", "They", "We", "You", "He", "She", "His", "Her",
            "My", "Your", "What", "When", "Where", "Who", "Why", "How", "Not", "No",
            "So", "As", "At", "By", "For", "From", "On", "One", "Then", "Now", "All",
            "Do", "Did", "Does", "Is", "Was", "Were", "Be", "Been", "Have", "Has",
            "Had", "Will", "Would", "Can", "Could", "May", "Might", "Must", "Should"}
TERM = re.compile(r"\b([A-Z][a-z’'\-]+(?:[ -][A-Z][a-z’'\-]+){0,3})\b")
IT_GROUP = re.compile(r"\b([A-ZÀÈÉÌÒÙ][a-zà-ÿ’'\-]+(?:[ -](?:[a-z]{1,4}[ -])?"
                       r"[A-ZÀÈÉÌÒÙ][a-zà-ÿ’'\-]+){0,3})\b")


def clean(t):
    t = re.sub(r"<[^<>\n]{1,40}>", " ", t)
    t = re.sub(r"\{[A-Z]+:[^}]*\}", " ", t)
    return t


def terms_of(t):
    """I nomi propri candidati: non a inizio frase, non parole di servizio."""
    out = set()
    for m in TERM.finditer(t):
        start = m.start()
        before = t[:start].rstrip()
        if not before or before[-1] in ".!?:;\n" or before.endswith(("«", "“", "'", '"')):
            continue                      # a inizio frase la maiuscola non dice nulla
        words = re.split(r"[ -]", m.group(1))
        if words[0] in FUNCTION_WORDS:
            continue
        out.add(m.group(1))
    return out


def main():
    minimum = 3
    if "--min" in sys.argv:
        minimum = int(sys.argv[sys.argv.index("--min") + 1])
    verbose = "-v" in sys.argv
    s = json.load(open(DICT, encoding="utf-8"))["strings"]
    gloss = json.load(open(GLOSSARY, encoding="utf-8"))
    known = set()
    for section in ("principi", "sapienze", "ruoli_e_luoghi", "ricorrenti"):
        known |= set(gloss.get(section, {}))
    known |= set(gloss.get("mai_tradurre", []))
    try:
        with open(VERIFIED, encoding="utf-8") as f:
            known |= {k for k in json.load(f) if not k.startswith("_")}
    except FileNotFoundError:
        pass

    where = collections.defaultdict(list)
    groups_of = {}
    overall = collections.Counter()
    for en, it in s.items():
        e, i = clean(en), clean(it)
        g = {m.group(1) for m in IT_GROUP.finditer(i) if len(m.group(1)) >= 4}
        groups_of[en] = (i, g)
        overall.update(g)
        for t in terms_of(e):
            where[t].append(en)

    # primo giro: quante volte ogni gruppo italiano ricorre con ogni termine
    count = collections.defaultdict(collections.Counter)
    for term, cases in where.items():
        if len(cases) < minimum or term in known:
            continue
        for en in cases:
            i, groups = groups_of[en]
            for g in sorted(groups):
                count[g][term] += 1
    # ogni gruppo appartiene al termine con cui ricorre di piu'
    # a parita' di conteggio most_common() sceglie in ordine d'inserimento, e
    # l'inserimento viene dall'iterazione di un set di stringhe: cioe' dal seed
    # di hash del processo. Su 'Brittany', con 2 rese a pari merito, lo stesso
    # comando diceva «nessun termine» o segnalava una divergenza a seconda del
    # seed. Il pareggio ora si rompe in ordine alfabetico, e il gate dice
    # sempre la stessa cosa.
    dominant = {g: min(c.items(), key=lambda kv: (-kv[1], kv[0]))[0]
                for g, c in count.items() if c}

    flagged = []
    for term, cases in where.items():
        if len(cases) < minimum or term in known:
            continue
        renderings = collections.Counter()
        per_rendering = collections.defaultdict(list)
        for en in cases:
            i, groups = groups_of[en]
            if re.search(r"\b%s\b" % re.escape(term), i):
                renderings["(invariato)"] += 1
                per_rendering["(invariato)"].append(en)
                continue
            for g in sorted(groups):
                if dominant.get(g) != term:
                    continue          # e' la resa di un altro termine
                if re.search(r"\b%s\b" % re.escape(g), clean(en)):
                    continue          # c'e' anche in inglese: non e' una resa
                renderings[g] += 1
                per_rendering[g].append(en)
        # Un candidato vale se compare soprattutto dove compare il termine: e'
        # cio' che distingue la sua resa dal contorno della frase.
        strong_ones = []
        for g, n in sorted(renderings.items(), key=lambda kv: (-kv[1], kv[0])):
            if n < 2:
                continue
            if g != "(invariato)" and n / max(1, overall[g]) < 0.66:
                continue
            if n / len(cases) < 0.15:
                continue
            strong_ones.append((g, n))
        distinct = []
        for g, n in strong_ones:
            if any(g in h or h in g or
                   difflib.SequenceMatcher(None, g.lower(), h.lower()).ratio() > 0.8
                   for h, _ in distinct):
                continue
            # varianti solo se si escludono: se compaiono nelle stesse stringhe
            # sono due cose diverse dette insieme, non due rese dello stesso nome
            ours = set(per_rendering[g])
            if any(len(ours & set(per_rendering[h])) > 0.2 * min(len(ours), len(per_rendering[h]))
                   for h, _ in distinct):
                continue
            distinct.append((g, n))
        if len(distinct) >= 2 and distinct[1][1] >= 2:
            flagged.append((term, len(cases), distinct, per_rendering))

    flagged.sort(key=lambda x: -x[1])
    print(f"{len(where)} termini dell'originale esaminati "
          f"(almeno {minimum} occorrenze, esclusi quelli gia' decisi nel glossario"
          f" e in {os.path.basename(VERIFIED)})\n")
    if not flagged:
        print("nessun termine reso in due modi diversi")
        return 0
    print(f"{len(flagged)} termini con piu' di una resa\n")
    for term, n, distinct, per_rendering in flagged:
        print(f"  {term!r} ({n} stringhe)")
        for g, k in distinct[: (8 if verbose else 4)]:
            print(f"      {k:3}x  {g!r}")
            if verbose:
                for en in per_rendering[g][:3]:
                    print(f"            {en[:90]}")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
