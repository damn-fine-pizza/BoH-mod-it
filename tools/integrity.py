"""Controlli d'integrita' tecnica su una traduzione: markup, template, token."""
import re, collections, sys
from bohloc import *

TAG   = re.compile(r"<[^<>\n]{1,40}>")
SETTING = re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
ASPECT_TMPL = re.compile(r"@#.*?@", re.S)
core, *_ = load_tree(CORE)

def check(name, root):
    idx, *_ = load_tree(root)
    prob = collections.Counter()
    examples = collections.defaultdict(list)
    for k, cv in core.items():
        lv = idx.get(k)
        if not lv: continue
        for f, en in cv["strings"].items():
            t = lv["strings"].get(f)
            if not t or not t.strip() or t.strip() == en.strip(): continue
            # Se l'originale e' vuoto non c'e' niente da confrontare: e' il caso
            # dello spazio lasciato libero nei crediti, che il mod francese usa
            # per firmarsi e che qui porta «Localizzazione Italiana». Senza
            # questa riga il confronto degli a-capo lo segnalava come difetto.
            if not en.strip(): continue
            # 1. tag TextMeshPro
            if collections.Counter(TAG.findall(en)) != collections.Counter(TAG.findall(t)):
                prob["tag markup alterati"] += 1
                examples["tag markup alterati"].append((k, f, en, t))
            # 2. token {SETTING:..}
            if set(SETTING.findall(en)) != set(SETTING.findall(t)):
                prob["token {SETTING} alterati"] += 1
                examples["token {SETTING} alterati"].append((k, f, en, t))
            # 3. prefisso $ di templating
            if en.startswith("$") != t.startswith("$"):
                prob["prefisso $ perso/aggiunto"] += 1
                examples["prefisso $ perso/aggiunto"].append((k, f, en, t))
            # 4. template aspetti @#id|testo#...@
            if bool(ASPECT_TMPL.search(en)) != bool(ASPECT_TMPL.search(t)):
                prob["template @#aspetto| rotto"] += 1
                examples["template @#aspetto| rotto"].append((k, f, en, t))
            elif ASPECT_TMPL.search(en):
                ids_en = re.findall(r"#([a-z0-9_.]*)\|", en)
                ids_t  = re.findall(r"#([a-z0-9_.]*)\|", t)
                if ids_en != ids_t:
                    prob["id aspetti nel template tradotti"] += 1
                    examples["id aspetti nel template tradotti"].append((k, f, en, t))
            # 5. token [further]
            if ("[further]" in en) != ("[further]" in t):
                prob["token [further] perso"] += 1
                examples["token [further] perso"].append((k, f, en, t))
            # 6. newline strutturali
            if en.count("\n") != t.count("\n"):
                prob["numero di a-capo diverso"] += 1
                examples["numero di a-capo diverso"].append((k, f, en, t))
    print(f"=== integrita' {name} ===")
    if not prob: print("  nessun problema rilevato")
    for p, n in prob.most_common():
        print(f"  {p}: {n}")
        for k, f, en, t in examples[p][:2]:
            print(f"      [{k[0]}/{k[1]}.{f}]")
            print(f"        EN: {en[:110]!r}")
            print(f"        XX: {t[:110]!r}")
    print()
    return sum(prob.values())

check("SPAGNOLO", ES)
check("FRANCESE", FR)
it_problems = check("ITALIANO", IT)

# l'esito vale solo per l'italiano: spagnolo e francese sono riferimenti, e i
# loro difetti (il [plus loin] tradotto del francese) non devono fermare noi.
sys.exit(1 if it_problems else 0)
