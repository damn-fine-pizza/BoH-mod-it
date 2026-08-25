"""Le label delle carte sono la forma autoritativa: la prosa deve usare quella.

Il nome di una carta compare due volte nel gioco: sulla carta (`label`) e nel
testo che la nomina. Se le due forme divergono, chi gioca legge «Acuti» in una
descrizione e poi cerca una carta che si chiama «Taglienti». E' l'incoerenza
piu' facile da notare e la piu' facile da misurare, perche' la forma giusta la
decide il gioco, non noi.

Il controllo: per ogni entita' del core con una label tradotta, si cercano le
stringhe di prosa che nominano la label inglese senza contenere quella italiana.

Le label ambigue si escludono per forza di cose: `Light`, `Wood`, `Glass` sono
parole inglesi ordinarie e compaiono ovunque. Si tengono solo le label lunghe o
composte, dove l'occorrenza nell'inglese e' quasi certamente un riferimento
alla carta.

La prosa flette: la carta si chiama «Bevanda» e il testo dice «Bevande
Preferite», la carta e' «Affaticamento» e il testo dice «Anima Affaticata».
Pretendere la label alla lettera segnalerebbe come divergenza ogni plurale e
ogni accordo - erano 294 segnalazioni, quasi tutte di questo tipo. Quindi il
confronto e' sulle radici: della resa italiana si prendono le parole piene
(niente articoli e preposizioni) e di ognuna il primo 60 % delle lettere, e si
chiede che la prosa le contenga tutte. «Affaticamento» -> «affatica», che sta
dentro «Affaticata»; «Taglienti» -> «taglie», che non sta dentro «Acuti», e
quella resta una divergenza vera.

    python3 tools/terms.py            elenca le divergenze
    python3 tools/terms.py -v         mostra anche le stringhe
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, CORE, load_tree

DICT = os.path.join(PROJ, "translations", "it.json")

# parole che non portano il senso: se la prosa le cambia non e' una divergenza
EMPTY = {"il","lo","la","i","gli","le","un","uno","una","del","dello","della","dei",
         "degli","delle","di","da","in","con","su","per","tra","fra","al","allo",
         "alla","ai","agli","alle","dal","dalla","nel","nella","che","ciò","cio",
         "e","ed","o","od","a","ad","è","non","si","mio","mia","suo","sua"}

def roots(it):
    """Le radici delle parole piene: il primo 60 % delle lettere, minimo quattro."""
    out = []
    for w in re.findall(r"[^\W\d_]+", it, re.UNICODE):
        wl = w.lower()
        if wl in EMPTY or len(wl) < 4:
            continue
        out.append(wl[:max(4, round(len(wl) * 0.6))])
    return out

def use_label(it, rendered):
    """La prosa nomina la carta, anche se la flette?"""
    if rendered in it:
        return True
    r = roots(rendered)
    if not r:
        return rendered.lower() in it.lower()
    bottom = it.lower()
    return all(x in bottom for x in r)

# label che non si possono usare come sonda: parole inglesi ordinarie, o forme
# che compaiono dentro altre label.
def useful(en, it):
    if en == it:                       # non tradotta: niente da confrontare
        return False
    if len(en) < 7:
        return False
    if "<" in en or "{" in en or "[" in en:
        return False
    words = en.split()
    if len(words) == 1 and en.islower():
        return False
    return True


def load():
    core, *_ = load_tree(CORE)
    d = json.load(open(DICT, encoding="utf-8"))["strings"]
    label = {}
    for (cat, eid), rec in core.items():
        en = rec["strings"].get("label")
        if not en:
            continue
        it = d.get(en)
        if it and useful(en, it):
            label.setdefault(en, (it, f"{cat}/{eid}"))
    return d, label


def main():
    verbose = "-v" in sys.argv
    d, label = load()
    print(f"{len(label)} label traducibili usate come sonda\n")
    # una label puo' apparire dentro un'altra piu' lunga: si cerca la piu' lunga
    sorted_ones = sorted(label, key=len, reverse=True)
    # indice per prima parola: senza, sono 12.639 x 2.000 ricerche e ci mette minuti
    per_word = collections.defaultdict(list)
    for lab in sorted_ones:
        per_word[lab.split()[0].lower()].append(lab)
    border = {lab: re.compile(r"(?<![\w'’])" + re.escape(lab) + r"(?![\w'’])")
             for lab in sorted_ones}
    prob = collections.defaultdict(list)
    for en, it in d.items():
        words = {w.lower() for w in re.findall(r"[\w'’-]+", en)}
        candidate = [lab for w in words & per_word.keys() for lab in per_word[w]]
        candidate.sort(key=len, reverse=True)
        for lab in candidate:
            if lab == en:
                continue                       # e' la label stessa
            if not border[lab].search(en):
                continue
            rendered = label[lab][0]
            if use_label(it, rendered):
                break                          # a posto: la prosa usa la label
            prob[lab].append((en, it))
            break
    if not prob:
        print("nessuna divergenza fra le label e la prosa")
        return 0
    tot = sum(len(v) for v in prob.values())
    print(f"{tot} stringhe nominano una carta senza usarne la label italiana\n")
    for lab in sorted(prob, key=lambda k: -len(prob[k])):
        rendered, where = label[lab]
        print(f"  {lab!r} -> {rendered!r}   [{where}]: {len(prob[lab])}")
        for en, it in prob[lab][: (8 if verbose else 2)]:
            m = re.search(re.escape(lab), en)
            print(f"      EN …{en[max(0,m.start()-45):m.end()+45]}…")
            print(f"      IT {it[:130]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
