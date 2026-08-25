"""Applica al dizionario le correzioni che tornano da una revisione esterna.

`review.py` costruisce il pacchetto da mandare a chi rilegge; questo e' il
ritorno. Prende il JSONL della risposta e lo applica, ma solo dove il testo di
partenza combacia ancora con quello che il revisore aveva davanti.

Il confronto con `it_attuale` non e' pignoleria. Fra il pacchetto e la risposta
il dizionario si muove, e una correzione applicata a una resa cambiata nel
frattempo cancella in silenzio il lavoro fatto dopo: sono proprio le stringhe
piu' toccate, cioe' quelle su cui si era gia' tornati.

Ogni proposta passa anche per validate.py e prose.py prima di entrare: una resa
che violerebbe il glossario o l'ortotipografia non si applica, per quanto sia
convincente la motivazione. E cio' che si decide di non accogliere si scrive in
translations/revisione-respinte.json con la ragione, come gia' fanno
identiche-volute.json e coerenza-verificate.json: cosi' la revisione dopo si
pre-filtra da sola invece di riproporre le stesse cose una terza volta.

Uso:
    python3 tools/revise.py revisione.jsonl                  il triage
    python3 tools/revise.py revisione.jsonl --mostra         le segnalazioni una per una
    python3 tools/revise.py revisione.jsonl --famiglie       chi ripete la stessa motivazione
    python3 tools/revise.py revisione.jsonl --apply --gravita alta

Le label d'interfaccia non passano dal dizionario: --apply le riscrive in
content/cultures/culture.json, che e' scritto a mano e non si rigenera.
    python3 tools/revise.py revisione.jsonl --respingi "la ragione"

Selettori, si combinano fra loro:
    --gravita alta|media|bassa
    --categoria controsenso|termine|registro|incoerenza|grammatica|genere
    --ampiezza punteggiatura|funzionali|corte|medie|lunghe|riscritture
    --cerca REGEX        sulla chiave inglese
    --righe 12,44,90     le righe del JSONL, quando la scelta e' stata fatta a mano
    --fermate            solo quelle che i gates non fanno passare
    --tutto              nessun filtro: --apply e --respingi non lavorano al buio

Le fermate per «genere fissato» sono quasi sempre battute di visitatori, e li'
la regola del neutro non si applica (convenzioni 5-ter): si scioglie esentando
la chiave inglese in `neutro_non_si_applica`, dentro il glossario, dopo aver
verificato che l'originale dia davvero un genere a chi parla.
"""
import argparse, collections, difflib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prose, validate
from bohloc import CORE, CULTURE_IT, PROJ, read

DICT = os.path.join(PROJ, "translations", "it.json")
REJECTED = os.path.join(PROJ, "translations", "revisione-respinte.json")
FIELDS = ("en", "it_attuale", "it_proposto", "categoria", "gravita", "perche")
NOTE = ("Le segnalazioni di una revisione esterna che il progetto ha letto e non "
        "accolto, con la ragione accanto. tools/revise.py le legge e non le "
        "ripropone: una decisione presa si scrive una volta sola, e la revisione "
        "successiva parte da qui invece di ricominciare da capo.")

# --- l'ampiezza dell'intervento -------------------------------------------
# Non e' la gravita' dichiarata dal revisore: e' quanto testo si muove. Serve a
# separare cio' che si puo' guardare in blocco - un articolo, una virgola - da
# cio' che chiede una lettura, e le due cose non coincidono affatto: fra le
# segnalazioni «bassa» ci sono riscritture intere, fra le «alta» ci sono refusi.
TOKEN = re.compile(r"\w+|\S", re.UNICODE)
PUNCTUATION = set("«»“”’'-–—,.;:!?()[]…")
FUNCTION_WORDS = {
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "del", "dello", "della",
    "dei", "degli", "delle", "al", "allo", "alla", "ai", "agli", "alle", "dal",
    "dalla", "dai", "nel", "nella", "nei", "negli", "nelle", "di", "a", "da", "in",
    "con", "su", "per", "tra", "fra", "e", "ed", "o", "che", "è", "l’", "dell’",
    "all’", "un’", "d’", "nell’", "sull’",
}
WIDTHS = ["punteggiatura", "funzionali", "corte", "medie", "lunghe", "riscritture"]
WIDTH_LABEL = {
    "punteggiatura": "solo punteggiatura",
    "funzionali":    "articoli e preposizioni",
    "corte":         "1-2 parole",
    "medie":         "3-6 parole",
    "lunghe":        "7-15 parole",
    "riscritture":   "riscritture (oltre 15 parole)",
}


def width(before, after):
    """Quanto si muove fra le due rese -> una delle classi di WIDTHS."""
    a, b = TOKEN.findall(before), TOKEN.findall(after)
    moved = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "equal":
            moved.append((a[i1:i2], b[j1:j2]))
    size = max(sum(len(a_side) for a_side, _ in moved),
               sum(len(b_side) for _, b_side in moved))
    words = [t.lower() for pair in moved for x in pair for t in x]
    if not words:
        return "punteggiatura"
    if all(t in PUNCTUATION for t in words):
        return "punteggiatura"
    if all(t in PUNCTUATION or t in FUNCTION_WORDS for t in words):
        return "funzionali"
    return "corte" if size <= 2 else "medie" if size <= 6 else \
           "lunghe" if size <= 15 else "riscritture"


# --- lettura e classificazione --------------------------------------------
def load(path):
    """Il JSONL della revisione -> lista di segnalazioni, con la riga di origine."""
    out = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}:{n} non e' JSON: {e}")
        missing = [f for f in FIELDS if f not in item]
        if missing:
            raise SystemExit(f"{path}:{n} manca {', '.join(missing)}")
        item["origine"] = n
        out.append(item)
    return out


def load_rejected():
    if not os.path.exists(REJECTED):
        return {}
    return {k: v for k, v in json.load(open(REJECTED, encoding="utf-8")).items()
            if not k.startswith("_")}


def ui_italian():
    """Le label d'interfaccia italiane, per testo inglese: dice quali sono fatte."""
    try:
        en = read(os.path.join(CORE, "cultures", "en", "culture.json"))["cultures"][0]["uilabels"]
        it = read(CULTURE_IT)["cultures"][0].get("uilabels", {})
        return {text: it[key] for key, text in en.items() if key in it}
    except Exception:
        return {}


def ui_labels():
    """I testi inglesi delle label d'interfaccia, che non passano dal dizionario.

    Stanno in core/cultures/en/culture.json per id; il culture del mod porta le
    rese italiane. Il confronto va fatto sull'inglese, che e' cio' che il
    revisore aveva davanti in interfaccia.json.
    """
    try:
        labels = read(os.path.join(CORE, "cultures", "en", "culture.json"))
        return set(labels["cultures"][0].get("uilabels", {}).values())
    except Exception:
        return set()


def classify(items, strings, labels, rejected, italian=None):
    """Aggiunge a ogni segnalazione lo stato e l'ampiezza. In loco."""
    italian = {} if italian is None else italian
    for item in items:
        en, before, after = item["en"], item["it_attuale"], item["it_proposto"]
        item["ampiezza"] = width(before, after)
        if en in rejected:
            item["stato"], item["nota"] = "respinta", rejected[en]
        elif en not in strings:
            # le label d'interfaccia non stanno nel dizionario: lo stato si legge
            # sul culture del mod, o non si saprebbe mai quali restano da fare
            if en not in labels:
                item["stato"] = "sconosciuta"
            elif italian.get(en) == after:
                item["stato"] = "gia' applicata (interfaccia)"
            elif italian.get(en, before) != before:
                item["stato"] = "deriva (interfaccia)"
            else:
                item["stato"] = "interfaccia"
        elif strings[en] == after:
            item["stato"] = "gia' applicata"
        elif strings[en] == before:
            item["stato"] = "applicabile"
        else:
            item["stato"] = "deriva"
    return items


def gates(items):
    """Quali proposte i gates non farebbero passare -> {riga di origine: motivo}.

    Si confronta con la resa attuale, non in assoluto: una stringa che gia' viola
    qualcosa non e' colpa della proposta, e bocciarla lascerebbe l'errore dov'e'.
    """
    rules = validate.load_rules()
    def marks(pairs):
        found = collections.defaultdict(set)
        for name, cases in validate.analyze(pairs, rules).items():
            for en, it in cases:
                found[en].add(name)
        return found
    before = marks([(i["en"], i["it_attuale"]) for i in items])
    after = marks([(i["en"], i["it_proposto"]) for i in items])
    out = {}
    for item in items:
        fresh = after.get(item["en"], set()) - before.get(item["en"], set())
        if fresh:
            out[item["origine"]] = sorted(fresh)[0]
    # l'ortotipografia: prose.py sa gia' riscrivere, quindi una proposta che
    # sbaglia le virgolette non e' un veto, e' una riga da far passare di li'.
    for name, cases in prose.review([(i["en"], i["it_proposto"]) for i in items]).items():
        keys = {en for en, _, _ in cases}
        for item in items:
            if item["en"] in keys and item["origine"] not in out:
                out[item["origine"]] = f"ortotipografia da sistemare: {name}"
    return out


def select(items, opt, blocked):
    """Le segnalazioni che i selettori lasciano passare."""
    out = items
    if opt.fermate:
        out = [i for i in out if i["origine"] in blocked]
    if opt.gravita:
        out = [i for i in out if i["gravita"] == opt.gravita]
    if opt.categoria:
        out = [i for i in out if i["categoria"] == opt.categoria]
    if opt.ampiezza:
        out = [i for i in out if i["ampiezza"] == opt.ampiezza]
    if opt.cerca:
        rx = re.compile(opt.cerca, re.I)
        out = [i for i in out if rx.search(i["en"])]
    if opt.righe:
        wanted = {int(n) for n in opt.righe.replace(" ", "").split(",") if n}
        out = [i for i in out if i["origine"] in wanted]
    return out


# --- le tre uscite ---------------------------------------------------------
def triage(items, blocked):
    print(f"{len(items)} segnalazioni\n")
    print("  stato rispetto al dizionario di oggi")
    for name, n in collections.Counter(i["stato"] for i in items).most_common():
        print(f"    {n:5}  {name}")
    print("\n  categoria per gravita'")
    grid = collections.defaultdict(collections.Counter)
    for i in items:
        grid[i["categoria"]][i["gravita"]] += 1
    print(f"    {'':14}{'alta':>6}{'media':>7}{'bassa':>7}{'tot':>7}")
    for name in sorted(grid, key=lambda k: -sum(grid[k].values())):
        row = grid[name]
        print(f"    {name:14}{row['alta']:>6}{row['media']:>7}{row['bassa']:>7}"
              f"{sum(row.values()):>7}")
    print("\n  ampiezza dell'intervento")
    sizes = collections.Counter(i["ampiezza"] for i in items)
    for name in WIDTHS:
        if sizes[name]:
            print(f"    {sizes[name]:5}  {WIDTH_LABEL[name]}")
    ready = [i for i in items if i["stato"] == "applicabile" and i["origine"] not in blocked]
    print(f"\n  {len(ready)} si applicano subito, {len(blocked)} le fermano i gates")
    if blocked:
        for why, n in collections.Counter(blocked.values()).most_common(6):
            print(f"    {n:5}  {why}")


def show(items, blocked, how_many=40):
    for item in items[:how_many]:
        stop = blocked.get(item["origine"])
        flag = f"  [FERMATA: {stop}]" if stop else ""
        print(f"[{item['gravita']}/{item['categoria']}/{item['stato']}]{flag}")
        print(f"  EN {item['en'][:110]}")
        print(f"   - {item['it_attuale'][:110]}")
        print(f"   + {item['it_proposto'][:110]}")
        print(f"   ? {item['perche'][:160]}\n")
    if len(items) > how_many:
        print(f"... e altre {len(items) - how_many}")


def families(items, least=3):
    """Le segnalazioni che ripetono la stessa motivazione: una decisione, non venti."""
    groups = collections.defaultdict(list)
    for item in items:
        groups[item["perche"].strip()].append(item)
    big = sorted((g for g in groups.values() if len(g) >= least), key=len, reverse=True)
    covered = sum(len(g) for g in big)
    print(f"{len(big)} famiglie da {least} segnalazioni in su, {covered} segnalazioni in tutto")
    print(f"{len(items) - covered} restano isolate\n")
    for group in big:
        head = group[0]
        print(f"  {len(group):4}  [{head['gravita']}] {head['perche'][:120]}")
        print(f"        es.  - {head['it_attuale'][:80]}")
        print(f"             + {head['it_proposto'][:80]}")


# --- le due scritture ------------------------------------------------------
def ui_key(text):
    """Il testo inglese di una label -> il suo id (UI_...), o None."""
    try:
        labels = read(os.path.join(CORE, "cultures", "en", "culture.json"))
        return {v: k for k, v in labels["cultures"][0]["uilabels"].items()}.get(text)
    except Exception:
        return None


def apply_ui(items):
    """Le label d'interfaccia, che stanno in culture.json e non nel dizionario.

    Quel file nessuno lo rigenera: e' scritto a mano, con tabulazioni e spazi
    mescolati, e riscriverlo con json.dump lo riformatterebbe tutto. Si sostituisce
    il valore dentro la sua riga, e il resto del file resta bit per bit com'era.
    """
    text = open(CULTURE_IT, encoding="utf-8-sig").read()
    done, missed = [], collections.Counter()
    for item in items:
        key = ui_key(item["en"])
        if not key:
            missed["label non trovata fra quelle inglesi"] += 1
            continue
        rx = re.compile(r'("' + re.escape(key) + r'"\s*:\s*)"((?:[^"\\]|\\.)*)"')
        m = rx.search(text)
        if not m:
            missed["label assente dal culture italiano"] += 1
        elif json.loads('"' + m.group(2) + '"') != item["it_attuale"]:
            missed["cambiata dopo la revisione"] += 1
        else:
            fresh = json.dumps(item["it_proposto"], ensure_ascii=False)
            text = text[:m.start()] + m.group(1) + fresh + text[m.end():]
            done.append(item)
    if done:
        open(CULTURE_IT, "w", encoding="utf-8").write(text)
    print(f"{len(done)} label d'interfaccia riscritte in "
          f"{os.path.relpath(CULTURE_IT, PROJ)}")
    for name, n in missed.most_common():
        print(f"  {n:5} saltate: {name}")
    return done


def apply_findings(items, blocked):
    d = json.load(open(DICT, encoding="utf-8"))
    strings, done, skipped = d["strings"], [], collections.Counter()
    for item in items:
        if item["stato"] != "applicabile":
            skipped[item["stato"]] += 1
        elif item["origine"] in blocked:
            skipped["fermata dai gates"] += 1
        elif strings.get(item["en"]) != item["it_attuale"]:
            skipped["cambiata mentre lavoravo"] += 1     # due --apply nella stessa tornata
        else:
            strings[item["en"]] = item["it_proposto"]
            done.append(item)
    if done:
        json.dump(d, open(DICT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
    print(f"{len(done)} correzioni applicate")
    for name, n in skipped.most_common():
        print(f"  {n:5} saltate: {name}")
    if done:
        print("\nadesso i gates: validate.py, prose.py, grammar.py, logic.py")
    return done


def reject(items, why):
    registry = {}
    if os.path.exists(REJECTED):
        registry = json.load(open(REJECTED, encoding="utf-8"))
    registry["_nota"] = NOTE
    fresh = 0
    for item in items:
        if item["en"] not in registry:
            fresh += 1
        registry[item["en"]] = why
    json.dump(registry, open(REJECTED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{fresh} segnalazioni scritte in {os.path.relpath(REJECTED, PROJ)}"
          f" ({len(items) - fresh} c'erano gia')")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("jsonl", help="la risposta della revisione")
    p.add_argument("--mostra", action="store_true")
    p.add_argument("--famiglie", action="store_true")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--respingi", metavar="RAGIONE")
    p.add_argument("--gravita", choices=("alta", "media", "bassa"))
    p.add_argument("--categoria")
    p.add_argument("--ampiezza", choices=WIDTHS)
    p.add_argument("--cerca", metavar="REGEX")
    p.add_argument("--righe", metavar="N,N,N")
    p.add_argument("--fermate", action="store_true")
    p.add_argument("--tutto", action="store_true")
    opt = p.parse_args(argv)

    items = load(opt.jsonl)
    strings = json.load(open(DICT, encoding="utf-8"))["strings"]
    classify(items, strings, ui_labels(), load_rejected(), ui_italian())
    blocked = gates(items)
    chosen = select(items, opt, blocked)
    filtered = len(chosen) != len(items)

    if (opt.apply or opt.respingi) and not filtered and not opt.tutto:
        raise SystemExit("--apply e --respingi su tutte le segnalazioni insieme "
                         "chiedono --tutto, scritto per esteso.")
    if opt.apply and opt.respingi:
        raise SystemExit("o si applica o si respinge, non tutte e due.")
    if opt.respingi:
        return 0 if reject(chosen, opt.respingi) is None else 0
    if opt.apply:
        apply_findings([i for i in chosen if i["stato"] != "interfaccia"], blocked)
        ui = [i for i in chosen if i["stato"] == "interfaccia"]
        if ui:
            apply_ui(ui)
        return 0
    if opt.famiglie:
        families(chosen)
        return 0
    if opt.mostra:
        show(chosen, blocked)
        return 0
    triage(chosen, {k: v for k, v in blocked.items()
                    if k in {i["origine"] for i in chosen}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
