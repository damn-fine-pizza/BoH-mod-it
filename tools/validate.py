"""Controlla il dizionario di traduzione: glossario, neutro, markup, glifi.

Va eseguito dopo ogni blocco tradotto, non alla fine: a posteriori diventa un
lavoro di bonifica, per blocco e' un gate.

I controlli stanno in analizza(), che lavora su una qualunque lista di coppie
(inglese, italiano): li usa anche checkpart.py per far autocontrollare a chi
traduce la propria slice, prima che il lavoro torni indietro.
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, CORE

DICT = os.path.join(PROJ, "translations", "it.json")
GLOSSARY = os.path.join(PROJ, "translations", "glossario.json")
TAG = re.compile(r"<[^<>\n]{1,40}>")
TOKEN = re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
ASPECT = re.compile(r"#([a-z0-9_.]*)\|")
SAINT = re.compile(r"\b(?:St|Saint)\.?\s[A-Z][a-zA-Z]+")
# participi e aggettivi che fisserebbero il genere di chi parla
# Solo pattern che fissano davvero il genere di CHI PARLA. "solo" avverbio e
# "una volta sola" non c'entrano: la prima versione li segnalava e produceva
# solo rumore.
MASCULINE = re.compile(
    # essere + participio in prima persona: "sono arrivato", "ero rimasta"
    r"\b(?:sono|ero|sarò|sarei|fui|mi sento|mi sentivo|mi ero|mi sono)\s+"
    r"(?:\w+\s+){0,2}\w{3,}(?:ato|uto|ito|ata|uta|ita)\b"
    # essere + aggettivo predicativo in prima persona. La parola che puo'
    # stare in mezzo e' un avverbio ("sono gia' pronto"), mai una preposizione:
    # «sono al sicuro» e «sono in salvo» sono locuzioni invariabili, e
    # segnalarle spingeva a scrivere «ho la sicurezza di», che non e' italiano.
    # `felic` e' uscito dalla lista per la stessa ragione al contrario: felice
    # e' epiceno, non fissa niente, e la segnalazione produceva «provo felicita'».
    r"|\b(?:sono|ero|mi sento|mi sentivo)\s+(?:(?!al |in |di |da )\w+\s+)?"
    r"(?:stanc|pront|sicur|content|solit|libere?|certo|convint|grat)[oaie]\b"
    # congiuntivo e condizionale col soggetto esplicito: "spera che io sia
    # arrivato". Senza "io" il pattern prenderebbe ogni terza persona, che qui
    # non c'entra: e' l'Archivista che non ha genere, non i visitatori.
    r"|\bio (?:sia|fossi|sarei|sarò|fui|ero)\s+(?:\w+\s+){0,2}\w{3,}(?:ato|uto|ito|ata|uta|ita)\b"
    # doppie forme esplicite
    r"|\b\w{3,}[oa]/[oa]\b|\b\w{3,}(?:ato|uto|ito)/a\b"
    # pronomi di terza persona con genere: l'inglese "this one" / "they" non ne ha,
    # e i personaggi cosi' descritti possono essere di qualunque genere.
    # In italiano il soggetto sottinteso e' la resa naturale e neutra.
    r"|\b(?:costui|costei|egli|ella|lui stesso|lei stessa)\b", re.I)
# virgolette dritte e apostrofo dritto: l'ortotipografia decisa e' «...» e ’
UPRIGHT = re.compile(r"[\"']")
# L'apostrofo tipografico usato come virgoletta d'apertura. Nasce dal correggere
# in blocco i ' dritti di una slice: gli apostrofi guariscono, le virgolette
# singole inglesi diventano ’cosi’ invece che «cosi». Sta a inizio stringa o
# dopo uno spazio; "anni ’20" e' un'altra cosa e non si tocca.
FAKE = re.compile(r"(?:^|(?<=\s))’(?!\d)")
# Il caporale usato come apostrofo: l«ultima, dell»Eternità. E' l'errore
# speculare, e nasce dallo stesso genere di correzione in blocco. Fra due
# lettere un caporale non ci sta mai: le virgolette hanno sempre uno spazio o
# una punteggiatura da un lato.
GUILLEMET_APOSTROPHE = re.compile(r"[a-zA-ZÀ-ÿ][«»][a-zA-ZÀ-ÿ]")


def load_rules():
    g = json.load(open(GLOSSARY, encoding="utf-8"))
    constraints = {}
    for section in ("principi", "sapienze", "ruoli_e_luoghi", "ricorrenti"):
        constraints.update(g[section])
    atlas = {int(x) for x in open(os.path.join(CORE, "_core.txt")).read().split(",")
             if x.strip().isdigit()}
    exceptions = {t: set(v) for t, v in g.get("eccezioni", {}).items()}
    forbidden = [(re.compile(k), v) for k, v in g.get("forme_vietate", {}).items()]
    # 5-bis vale per l'Archivista, non per i visitatori: MASCHILE non puo'
    # sapere chi parla, quindi le battute gia' verificate si esentano per
    # chiave inglese. Vedi la nota nel glossario.
    exempt = set(g.get("neutro_non_si_applica", {}))
    # Dal 0.1.9.5 il maschile non marcato e' ammesso dove la forma neutra costa
    # scorrevolezza (convenzioni 5-bis). Ammesso non vuol dire invisibile: ogni
    # riga che lo usa sta qui, con la ragione per cui la forma neutra non
    # reggeva, e si rilegge tutta insieme.
    exempt |= set(g.get("archivista_al_maschile", {}))
    return constraints, set(g["mai_tradurre"]), atlas, exceptions, forbidden, exempt


def analyze(pairs, rules=None):
    """coppie: iterabile di (inglese, italiano) -> {categoria: [(en, it), ...]}"""
    constraints, never, atlas, exceptions, forbidden, exempt = rules or load_rules()
    prob = collections.defaultdict(list)
    for en, it in pairs:
        # 1. markup
        if collections.Counter(TAG.findall(en)) != collections.Counter(TAG.findall(it)):
            prob["tag alterati"].append((en, it))
        if set(TOKEN.findall(en)) != set(TOKEN.findall(it)):
            prob["token {SETTING} alterati"].append((en, it))
        if en.startswith("$") != it.startswith("$"):
            prob["prefisso $"].append((en, it))
        if ASPECT.findall(en) != ASPECT.findall(it):
            prob["id aspetti nel template"].append((en, it))
        if ("[further]" in en) != ("[further]" in it):
            prob["token [further]"].append((en, it))
        if en.count("\n") != it.count("\n"):
            prob["a-capo"].append((en, it))
        # 2. glossario: se il termine c'e' in inglese, la resa decisa deve esserci.
        # Niente scappatoia "oppure c'e' il termine inglese": assolveva tutte le
        # stringhe non tradotte, ed e' il motivo per cui venticinque etichette
        # come "Edge: a Conquest!" sono passate per mesi. Dove il termine resta
        # in inglese apposta - i titoli dei brani, 'Sea's Edge' - si nomina la
        # stringa in `eccezioni`, una per una.
        for term, rendered in constraints.items():
            if en in exceptions.get(term, ()):
                continue          # qui il termine non e' il Principio
            if re.search(r"(?<![\w'])" + re.escape(term) + r"(?![\w'])", en):
                if rendered.lower() not in it.lower():
                    prob[f"glossario: {term} -> {rendered}"].append((en, it))
        # 3. termini da non tradurre: devono restare. Le `eccezioni` valgono
        # anche qui: «Henry» resta Henry per il personaggio del gioco, ma Henry
        # VIII e' un re realmente esistito e in italiano si chiama Enrico VIII,
        # come Elagabalus si chiama Eliogabalo (punto 2-bis).
        for term in never:
            if en in exceptions.get(term, ()):
                continue
            if re.search(r"(?<![\w'])" + re.escape(term) + r"(?![\w'])", en):
                if term not in it:
                    prob[f"non tradurre: {term}"].append((en, it))
        # 3-bis. santi e nomi propri: la forma inglese va conservata tale e quale
        # (convenzioni 2-bis). Il primo giro aveva prodotto sia "San Trifone" sia
        # "St Tryphon" per lo stesso nome, che e' esattamente il tipo di
        # incoerenza che si nota giocando.
        for shape in SAINT.findall(en):
            if shape not in it:
                prob["nome proprio italianizzato (St/Saint)"].append((en, it))
                break
        # 3-ter. forme che il progetto ha deciso di non usare. Il glossario non
        # le prende: "Vagabond" e' dentro "Vagabonda", e il genere di un nome
        # che resta invariato non si esprime con una coppia EN -> IT.
        for rx, why in forbidden:
            if rx.search(it):
                prob[f"forma vietata: {why[:60]}"].append((en, it))
        # 4. neutro
        m = MASCULINE.search(it)
        if m and en not in exempt and en.strip() not in exempt:
            prob["genere fissato (regola del neutro)"].append((en, it + f"   <<{m.group()}>>"))
        # 5. ortotipografia: apostrofo tipografico sempre, virgolette caporali.
        # I tag si tolgono prima: un <link='x'> non c'entra con la tipografia.
        if UPRIGHT.search(TAG.sub("", it)):
            prob["virgolette o apostrofo dritti"].append((en, it))
        if FAKE.search(it):
            prob["apostrofo al posto delle caporali"].append((en, it))
        if GUILLEMET_APOSTROPHE.search(it):
            prob["caporale al posto dell'apostrofo"].append((en, it))
        # 6. glifi
        outside = {c for c in it if ord(c) not in atlas}
        if outside:
            prob[f"glifi fuori atlante: {''.join(sorted(outside))}"].append((en, it))
    return prob


def show_report(prob, how_many=3):
    tot = sum(len(v) for v in prob.values())
    for k in sorted(prob, key=lambda k: -len(prob[k])):
        print(f"  {k}: {len(prob[k])}")
        for en, it in prob[k][:how_many]:
            print(f"      EN {en[:100]!r}\n      IT {it[:100]!r}")
    return tot


def main():
    d = json.load(open(DICT, encoding="utf-8"))
    prob = analyze(d["strings"].items())
    if not prob:
        print(f"{len(d['strings'])} stringhe: nessun problema")
        return 0
    tot = sum(len(v) for v in prob.values())
    print(f"{len(d['strings'])} stringhe tradotte, {tot} segnalazioni\n")
    show_report(prob)
    return 1


if __name__ == "__main__":
    sys.exit(main())
