"""Prepara il contesto di una slice: un campione scelto, non il dizionario intero.

Il problema che risolve. Il briefing chiedeva a ogni traduttore di leggere
translations/it.json "come esempio di registro". A 2.677 stringhe quel file pesa
gia' 154k token e a lavoro finito ne pesera' circa 735k, moltiplicati per ogni
agente di ogni giro. Ed e' anche un modo mediocre di dare il registro: un
dizionario in ordine alfabetico non e' un campione, e' un elenco.

Qui si costruisce un campione mirato: le coppie gia' approvate che hanno piu'
probabilita' di servire per QUESTA slice. Tre criteri, in ordine di peso:

 1. provenienza -- una stringa gia' tradotta che vive negli stessi file della
    slice parla degli stessi oggetti e usa lo stesso lessico;
 2. lessico condiviso -- sovrapposizione di parole piene, pesata per rarita'
    (una stringa che condivide "haustorial" vale piu' di una che condivide "make");
 3. forma -- il campione riproduce la distribuzione di lunghezze della slice, cosi'
    chi traduce label brevi vede label brevi e non solo prosa lunga.

Piu' il glossario ridotto ai termini che in questa slice compaiono davvero.

Circa 8k token per slice, e non cresce col dizionario.

Uso: python context.py 6 7 8 9 10
"""
import json, os, re, sys, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import load_tree, CORE, PROJ

PARTS = os.path.join(PROJ, "translations", "parts")
DICT  = os.path.join(PROJ, "translations", "it.json")
GLOSSARY  = os.path.join(PROJ, "translations", "glossario.json")

BUDGET = 22000          # caratteri di esempi, EN+IT

STOP = set("""the a an and or of to in on at for with from by as is are was were be
been being this that these those it its his her their our your my me he she they we
you not no if then than but so such which who whom what when where how all any some
more most other into over under out up down off again once here there will would can
could has have had do does did about after before between through during without""".split())
WORD = re.compile(r"[a-zA-Z][a-zA-Z'’-]{2,}")


def words(t):
    return [w.lower() for w in WORD.findall(t) if w.lower() not in STOP]


def shape(t):
    """0 = etichetta, 1 = frase, 2 = prosa."""
    n = len(t)
    return 0 if n < 45 else (1 if n < 180 else 2)


def show(t):
    """Gli a-capo reali spezzerebbero il formato a due righe: si mostrano escapati,
    che e' anche il modo giusto di ricordare a chi traduce che vanno contati."""
    return t.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "")


def needed(term, text):
    return re.search(r"(?<![\w'’])" + re.escape(term) + r"(?![\w'’])", text)


def core_index():
    """-> (chiave 'cat/id.campo' -> file, testo inglese -> {file, ...})"""
    core, *_ = load_tree(CORE)
    key2file, text2files = {}, collections.defaultdict(set)
    for (cat, eid), v in core.items():
        rel = v["file"].replace(os.sep, "/")
        for field, txt in v["strings"].items():
            key2file[f"{cat}/{eid}.{field}"] = rel
            t = txt.strip()
            if t:
                text2files[t].add(rel)
    return key2file, text2files


def choose(chunk, d, key2file, text2files, df, ndoc):
    """-> lista di (en, it) scelte, entro BUDGET caratteri."""
    vocab = collections.Counter()
    for e in chunk:
        vocab.update(set(words(e["en"])))
    weight_files = collections.Counter()
    for e in chunk:
        f = key2file.get(e["dove"])
        if f:
            weight_files[f] += 1
    tot_file = sum(weight_files.values()) or 1

    def score(en):
        ws = set(words(en))
        if not ws:
            return 0.0
        lex = sum(math.log(1 + ndoc / (1 + df[w])) * math.log(1 + vocab[w])
                  for w in ws if w in vocab)
        lex /= math.sqrt(len(ws) + 3)
        aff = sum(weight_files.get(f, 0) for f in text2files.get(en, ())) / tot_file
        return lex + 6.0 * aff

    # la slice detta la distribuzione delle forme; il campione la riproduce
    share = collections.Counter(shape(e["en"]) for e in chunk)
    n = len(chunk) or 1
    caps = {b: BUDGET * share[b] / n for b in (0, 1, 2)}

    per_shape = {0: [], 1: [], 2: []}
    for en, it in d.items():
        per_shape[shape(en)].append((score(en), en, it))
    choices, leftover = [], 0.0
    for b in (2, 1, 0):                      # la prosa per prima: costa di piu'
        spent, budget = 0, caps[b] + leftover
        for _, en, it in sorted(per_shape[b], key=lambda x: -x[0]):
            cost = len(en) + len(it) + 8
            if spent + cost > budget:
                continue
            choices.append((en, it))
            spent += cost
        leftover = max(0.0, budget - spent)
    return choices


def targeted_glossary(chunk, d, g):
    constraints = {}
    for section in ("principi", "sapienze", "ruoli_e_luoghi", "ricorrenti"):
        constraints.update(g[section])
    texts = [e["en"] for e in chunk]
    present = {t: r for t, r in constraints.items() if any(needed(t, x) for x in texts)}
    never = [t for t in g["mai_tradurre"] if any(needed(t, x) for x in texts)]
    examples = {}
    for t in present:
        samples = [(en, it) for en, it in d.items() if needed(t, en) and len(en) > 30]
        samples = [c for c in samples if 60 < len(c[0]) < 240] or samples
        samples.sort(key=lambda p: len(p[0]))
        examples[t] = samples[len(samples) // 2:][:1] if samples else []
    return present, never, examples


def write(n, chunk, choices, present, never, examples, key2file):
    total_words = sum(len(e["en"].split()) for e in chunk)
    files = collections.Counter(key2file.get(e["dove"], "?") for e in chunk)
    out = [f"# Contesto per la slice {n}",
           "",
           f"{len(chunk)} stringhe, ~{total_words} parole. Provengono da:",
           ""]
    for f, c in files.most_common(8):
        out.append(f"- `{f}` — {c} stringhe")
    out += ["",
            "Questo file sostituisce la lettura di `translations/it.json`, che è ",
            "troppo grande e in ordine alfabetico. Qui sotto c'è quello che serve: i ",
            "termini vincolanti che compaiono davvero in questa slice, e un campione ",
            "delle traduzioni già approvate scelte per affinità con il testo che devi ",
            "tradurre. **Non leggere `it.json`.**",
            ""]

    out += ["## Termini vincolanti presenti in questa slice", ""]
    if present:
        out += ["| inglese | italiano |", "|---|---|"]
        for t, r in sorted(present.items()):
            out.append(f"| {t} | **{r}** |")
    else:
        out.append("Nessuno dei termini fissati compare in questa slice.")
    out.append("")
    if never:
        out += ["## Da lasciare in inglese, identici", "",
                " · ".join(f"`{t}`" for t in sorted(never)), ""]

    alive = {t: e for t, e in examples.items() if e}
    alive = dict(sorted(alive.items(), key=lambda kv: len(kv[1][0][0]))[:10])
    if alive:
        out += ["## Gli stessi termini, visti in frase", ""]
        for t in sorted(alive):
            for en, it in alive[t]:
                out += [f"EN  {show(en)}", f"IT  {show(it)}", ""]

    out += [f"## Campione del registro già approvato ({len(choices)} coppie)", "",
            "Scelte per affinità con questa slice: stessi file, stesso lessico, stessa",
            "distribuzione di lunghezze. Servono a darti il tono, non a essere copiate.",
            ""]
    for en, it in choices:
        out += [f"EN  {show(en)}", f"IT  {show(it)}", ""]

    text = "\n".join(out)
    p = os.path.join(PARTS, f"contesto_{n}.md")
    open(p, "w", encoding="utf-8").write(text)
    return p, len(text), len(choices)


def main(numbers):
    d = json.load(open(DICT, encoding="utf-8"))["strings"]
    g = json.load(open(GLOSSARY, encoding="utf-8"))
    key2file, text2files = core_index()
    df = collections.Counter()
    for en in d:
        df.update(set(words(en)))
    ndoc = len(d) or 1

    for n in numbers:
        cp = os.path.join(PARTS, f"chunk_{n}.json")
        if not os.path.exists(cp):
            print(f"slice {n}: chunk_{n}.json non esiste")
            continue
        chunk = json.load(open(cp, encoding="utf-8"))
        choices = choose(chunk, d, key2file, text2files, df, ndoc)
        present, never, examples = targeted_glossary(chunk, d, g)
        p, car, n_pairs = write(n, chunk, choices, present, never, examples, key2file)
        print(f"{os.path.basename(p)}: {n_pairs} esempi, {car} caratteri "
              f"(~{car//4} token)   vincoli: {len(present)}   mai tradurre: {len(never)}")


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [1])
