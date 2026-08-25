"""Le stringhe italiane identiche all'inglese: quali sono scelte e quali sono buchi.

Il conto grosso di coverage.py non vede le stringhe che *sembrano* tradotte.
Qui si guardano tre cose che quel conto non distingue:

  1. l'uguaglianza esatta col core inglese;
  2. l'uguaglianza dopo aver normalizzato apostrofi, virgolette e lineette -
     una stringa mai tradotta a cui e' stato curvato l'apostrofo non e' piu'
     identica, e sfuggiva;
  3. la somiglianza (difflib > --threshold), che prende il resto.

Il verdetto lo danno le due localizzazioni di riferimento, come al punto 2-bis
delle convenzioni: se francese e spagnolo traducono entrambi, e' un buco; se
lasciano entrambi, e' una scelta; se divergono, decide il francese.

    python3 tools/identical.py                 il riepilogo e i buchi
    python3 tools/identical.py --all         anche le scelte e le somiglianti
    python3 tools/identical.py --fields         il conto per campo (punto 2)
    python3 tools/identical.py --json out.json i buchi in forma lavorabile
"""
import sys, json, collections, difflib, re, unicodedata
from bohloc import *

VISIBLE = {"label", "desc", "startdescription"}
THRESHOLD = 0.93

def surfaces(root):
    """Per ogni entita' del core, che cosa ne vede chi gioca.

    Un 'desc' non e' visibile per il fatto di chiamarsi desc: la desc di un
    Principio si legge davvero, quella di un aspetto marcato 'ishidden' o
    'noartneeded' no, perche' quell'aspetto non compare mai. Il dato lo da' il
    core, non il nome del campo."""
    out = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".json") or "_legacy_" in fn:
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            cat = rel.split(os.sep)[0]
            try:
                data = read(os.path.join(dirpath, fn))
            except Exception:
                continue
            for _, ent in entities(data):
                eid = ent.get("id") or ent.get("ID")
                if not isinstance(eid, str):
                    continue
                low = {k.lower(): v for k, v in ent.items()}
                if low.get("ishidden"):
                    s = "nascosto"
                elif low.get("noartneeded"):
                    s = "senza arte"
                elif low.get("isaspect"):
                    s = "aspetto"
                else:
                    s = "carta" if cat == "elements" else cat[:-1] if cat.endswith("s") else cat
                out[(cat, eid.lower())] = s
    return out

INVISIBLE = {"nascosto", "senza arte"}

def normalize(s):
    """Toglie le differenze che non sono traduzione: apostrofi, virgolette, lineette."""
    s = unicodedata.normalize("NFC", s)
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("«", '"'), ("»", '"'), ("–", "-"), ("—", "-"),
                 ("…", "..."), (" ", " ")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()

def similarity(a, b):
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def words(s):
    return [w for w in re.findall(r"[^\W\d_]+", normalize(s), re.UNICODE) if w]

def touched(en, it):
    """Almeno una parola e' cambiata: la stringa e' stata tradotta, non copiata.

    Serve per le famiglie che somigliano legittimamente all'inglese - 'Craft: X'
    -> 'Crea: X' con X nome proprio, o i cognati (Ingredient/Ingrediente). Il
    caso opposto - stessa parola, apostrofo curvato - non ha parole diverse ed
    e' un buco."""
    a, b = words(en), words(it)
    sm = difflib.SequenceMatcher(None, a, b)
    return any(tag != "equal" for tag, *_ in sm.get_opcodes())

def translates(en, other):
    """L'altra localizzazione ha tradotto questa stringa?"""
    if other is None or not other.strip():
        return None                      # non ce l'ha: non vota
    return normalize(other) != normalize(en) and similarity(normalize(en), normalize(other)) <= THRESHOLD

INTENDED = os.path.join(PROJ, "translations", "identiche-volute.json")

def intended():
    """Le stringhe gia' verificate che restano in inglese apposta, con la ragione."""
    try:
        with open(INTENDED, encoding="utf-8") as f:
            return {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    except FileNotFoundError:
        return {}

def main():
    threshold = THRESHOLD
    if "--threshold" in sys.argv:
        threshold = float(sys.argv[sys.argv.index("--threshold") + 1])
    log = intended()
    core, *_ = load_tree(CORE)
    surface_of = surfaces(CORE)
    it, *_ = load_tree(IT)
    es, *_ = load_tree(ES)
    fr, *_ = load_tree(FR)

    # per ogni testo inglese distinto: le occorrenze che in italiano non si sono mosse
    cases = collections.defaultdict(lambda: {"occ": [], "es": collections.Counter(),
                                            "fr": collections.Counter(), "tipo": ""})
    n_fields = collections.Counter()          # per il punto 2
    fields_by_kind = collections.defaultdict(collections.Counter)
    for key, cv in core.items():
        lv = it.get(key)
        if lv is None:
            continue
        for field, en in cv["strings"].items():
            t = lv["strings"].get(field)
            if t is None or not t.strip():
                continue
            if t.strip() == en.strip():
                kind = "identica"
            elif normalize(t) == normalize(en):
                kind = "normalizzata"
            elif similarity(en, t) > threshold:
                kind = "toccata" if touched(en, t) else "somigliante"
            else:
                continue
            c = cases[en]
            c["occ"].append((key, field, kind, t))
            c.setdefault("sup", collections.Counter())[surface_of.get(key, "?")] += 1
            n_fields[kind] += 1
            fields_by_kind[kind][field.split(".")[0]] += 1
            for name, tree in (("es", es), ("fr", fr)):
                v = tree.get(key, {}).get("strings", {}).get(field) if tree.get(key) else None
                vote = translates(en, v)
                if vote is not None:
                    c[name][vote] += 1
                    if vote and "resa_" + name not in c:
                        c["resa_" + name] = v

    # verdetto per testo distinto
    holes, choices, diverging, recorded, touched_ones = [], [], [], [], []
    for en, c in cases.items():
        es_trad = c["es"][True] > c["es"][False]
        fr_trad = c["fr"][True] > c["fr"][False]
        c["visibili"] = sum(1 for k, field, _, _ in c["occ"]
                            if field.split(".")[0] in VISIBLE and surface_of.get(k) not in INVISIBLE)
        c["en"] = en
        if en in log:
            c["verdetto"] = "voluta"; c["ragione"] = log[en]; recorded.append(c); continue
        if all(o[2] == "toccata" for o in c["occ"]):
            c["verdetto"] = "tradotta (somiglia e basta)"; touched_ones.append(c); continue
        if es_trad and fr_trad:
            c["verdetto"] = "BUCO"; holes.append(c)
        elif not es_trad and not fr_trad:
            c["verdetto"] = "scelta"; choices.append(c)
        else:
            c["verdetto"] = "BUCO (solo FR)" if fr_trad else "scelta (FR lascia)"
            diverging.append(c)

    sort_key = lambda l: sorted(l, key=lambda c: (-c["visibili"], -len(c["occ"]), c["en"][:40]))
    tot_occ = lambda l: sum(len(c["occ"]) for c in l)

    print("=== quanto e' rimasto fermo sull'inglese ===")
    print(f"  {len(cases)} testi distinti, {sum(n_fields.values())} campi nei file del mod")
    for kind in ("identica", "normalizzata", "somigliante", "toccata"):
        if n_fields[kind]:
            det = ", ".join(f"{k} {v}" for k, v in fields_by_kind[kind].most_common(6))
            print(f"    {kind:13} {n_fields[kind]:5} campi   ({det})")
    vis = sum(c["visibili"] for c in cases.values())
    per_surface = collections.Counter()
    for c in cases.values(): per_surface.update(c["sup"])
    print(f"  su superfici che chi gioca vede (label/desc/startdescription di entita' non nascoste):"
          f" {vis} campi su {sum(n_fields.values())}")
    print("  per superficie: " + ", ".join(f"{k} {v}" for k, v in per_surface.most_common()))
    print(f"\n  buchi:      {len(holes):4} testi / {tot_occ(holes):5} campi   (FR ed ES traducono entrambi)")
    print(f"  divergenti: {len(diverging):4} testi / {tot_occ(diverging):5} campi   (decide il francese)")
    print(f"  scelte:     {len(choices):4} testi / {tot_occ(choices):5} campi   (FR ed ES lasciano entrambi)")
    print(f"  volute:     {len(recorded):4} testi / {tot_occ(recorded):5} campi   (gia' verificate, in {os.path.basename(INTENDED)})")
    print(f"  tradotte:   {len(touched_ones):4} testi / {tot_occ(touched_ones):5} campi   (somigliano all'inglese ma sono tradotte)")

    if "--fields" in sys.argv:
        print("\n=== per campo (tutti i tipi) ===")
        tot = collections.Counter()
        for kind in fields_by_kind:
            tot.update(fields_by_kind[kind])
        for field, n in tot.most_common():
            marker = "  <- si vede" if field in VISIBLE else ""
            print(f"    {field:22} {n:5}{marker}")

    def show_report(title, show_list):
        print(f"\n=== {title} ({len(show_list)}) ===")
        for c in sort_key(show_list):
            occ = c["occ"]
            fields = collections.Counter(field.split(".")[0] for _, field, _, _ in occ)
            print(f"\n  EN: {c['en'][:150]!r}")
            print(f"      IT: {occ[0][3][:150]!r}")
            if c.get("resa_fr"): print(f"      FR: {c['resa_fr'][:110]!r}")
            if c.get("resa_es"): print(f"      ES: {c['resa_es'][:110]!r}")
            print(f"      {len(occ)} campi ({', '.join(f'{k} {v}' for k, v in fields.most_common())})"
                  f"  visibili: {c['visibili']}  {occ[0][2]}"
                  f"  [{', '.join(f'{k} {v}' for k, v in c['sup'].most_common())}]")
            for key, field, _, _ in occ[:3]:
                print(f"        {key[0]}/{key[1]}  {field}")
            if len(occ) > 3: print(f"        ... e altri {len(occ)-3}")

    show_report("BUCHI da chiudere", holes + [c for c in diverging if c["verdetto"].startswith("BUCO")])
    if "--all" in sys.argv:
        show_report("volute: verificate e registrate", recorded)
        show_report("tradotte: somigliano all'inglese ma sono state tradotte", touched_ones)
        show_report("scelte: FR ed ES lasciano l'inglese", choices)
        show_report("scelte: divergono, il francese lascia", [c for c in diverging if not c["verdetto"].startswith("BUCO")])

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        rows = [{"en": c["en"], "it": c["occ"][0][3], "fr": c.get("resa_fr"), "es": c.get("resa_es"),
                 "campi": len(c["occ"]), "visibili": c["visibili"], "tipo": c["occ"][0][2],
                 "verdetto": c["verdetto"],
                 "esempi": [f"{k[0]}/{k[1]}#{field}" for k, field, _, _ in c["occ"][:5]]}
                for c in sort_key(holes + diverging + choices + recorded + touched_ones)]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f"\nscritti {len(rows)} testi in {out}")

    # esito da gate: i buchi sono un difetto, le scelte no
    return 1 if holes or [c for c in diverging if c["verdetto"].startswith("BUCO")] else 0



if __name__ == "__main__":
    sys.exit(main())
