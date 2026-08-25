"""Compone i titoli dei libri nella forma «titolo inglese (traduzione)».

Le copertine dei 281 libri hanno impresse le iniziali del titolo inglese.
Tradurre il titolo romperebbe quella corrispondenza, quindi si tiene l'inglese
e si affianca la traduzione, come fa la localizzazione francese.

Regole, dedotte dal francese:
  1. titolo semplice   -> «EN (IT)»
  2. l'inglese ha gia' una qualificazione fra parentesi
                       -> «EN-base (IT-base) - Qualificazione» (non si annidano)
  3. suffisso di volume-> resta in coda: «EN (IT), vol 1»
  4. titolo in latino o in lingua inventata, che non si traduce
                       -> invariato, senza parentesi

Gli agenti traducono il titolo normalmente; la forma la compone questo
strumento, che e' idempotente e si puo' rieseguire senza danno.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import load_tree, CORE, PROJ

DICT = os.path.join(PROJ, "translations", "it.json")
VOL = re.compile(r",\s*(vol\.?\s*\d+|libro\s*\d+|book\s*\d+)\s*$", re.I)
QUALIFIER = re.compile(r"^(.*?)\s*\(([^()]+)\)\s*$")

def decompose(t):
    vol = None
    m = VOL.search(t)
    if m:
        vol = m.group(1); t = t[:m.start()]
    qualifier = None
    m = QUALIFIER.match(t)
    if m:
        t, qualifier = m.group(1), m.group(2)
    return t.strip(), qualifier, vol

def compose(en, it):
    if it.strip() == en.strip():
        return en
    if re.match(r"^[A-Z\s]+$", en.strip()) and len(en.split()) > 1:
        return en
    base_en, qual_en, vol_en = decompose(en)
    base_it, qual_it, vol_it = decompose(it)
    if base_it == base_en and not qual_it:
        return en
    out = f"{base_en} ({base_it})"
    q = qual_it or qual_en
    if q:
        out += f" - {q}"
    v = vol_en or vol_it
    if v:
        out += f", {v}"
    return out

def book_titles():
    core, *_ = load_tree(CORE)
    return {v["strings"]["label"].strip()
            for k, v in core.items()
            if k[0] == "elements" and k[1].startswith("t.") and v["strings"].get("label")}

def main(dry=False):
    titles = book_titles()
    d = json.load(open(DICT, encoding="utf-8"))
    done_ones = already = 0
    for en in sorted(titles):
        it = d["strings"].get(en)
        if not it:
            continue
        if it.startswith(decompose(en)[0]):
            already += 1; continue
        fresh_one = compose(en, it)
        if fresh_one != it:
            if done_ones < 8:
                print(f"   {en[:52]!r}\n      {it[:62]!r}\n   -> {fresh_one[:80]!r}")
            if not dry:
                d["strings"][en] = fresh_one
            done_ones += 1
    print(f"\ntitoli nel gioco: {len(titles)} | composti ora: {done_ones} | gia' a posto: {already}")
    if not dry:
        json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)

if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
