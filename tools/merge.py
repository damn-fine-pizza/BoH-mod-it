"""Fonde i file prodotti dagli agenti nel dizionario, con controlli.

Tre cose possono andare storte e vanno intercettate qui, non dopo:
 - una chiave non combacia con nessuna stringa inglese reale (spazi, virgolette
   normalizzate, troncature): la traduzione andrebbe persa in silenzio;
 - due agenti hanno tradotto la stessa stringa in modo diverso;
 - un agente ha riscritto una stringa gia' presente nel dizionario.

Uso: python merge.py [--dry]
"""
import json, glob, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import load_tree, CORE, PROJ

DICT = os.path.join(PROJ, "translations", "it.json")
PARTS = os.path.join(PROJ, "translations", "parts")

def main(dry=False):
    core, *_ = load_tree(CORE)
    real_ones = {t.strip() for v in core.values() for t in v["strings"].values() if t.strip()}
    d = json.load(open(DICT, encoding="utf-8"))

    fresh_ones, orphans, collisions, rewrites = {}, [], [], []
    origin = {}
    # solo le slice unite: part_12.json si', part_12.003.json no. I frammenti
    # sono il lavoro in corso di un agente, non ancora passato dal suo
    # autocontrollo, e finche' esistono la slice non e' finita.
    slices = [p for p in sorted(glob.glob(os.path.join(PARTS, "part_*.json")))
             if re.fullmatch(r"part_\d+\.json", os.path.basename(p))]
    fragments = len(glob.glob(os.path.join(PARTS, "part_*.*.json")))
    if fragments:
        print(f"  attenzione: {fragments} frammenti ancora in giro, "
              f"qualcuno sta traducendo. Le loro slice restano fuori.")
    for p in slices:
        name = os.path.basename(p)
        try:
            part = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  {name}: JSON illeggibile: {str(e)[:80]}")
            continue
        for en, it in part.items():
            k = en.strip()
            if k not in real_ones:
                orphans.append((name, en)); continue
            if not it or not it.strip():
                continue
            if k in d["strings"] and d["strings"][k] != it:
                rewrites.append((name, en, d["strings"][k], it)); continue
            if k in fresh_ones and fresh_ones[k] != it:
                collisions.append((origin[k], name, en, fresh_ones[k], it)); continue
            fresh_ones[k] = it; origin[k] = name
        print(f"  {name}: {len(part)} coppie")

    # "nuove" conteneva anche le coppie identiche a quelle gia' fissate: erano
    # conferme, non stringhe in piu', e gonfiavano il numero di due volte e mezzo.
    unseen = sum(1 for k in fresh_ones if k not in d["strings"])
    print(f"\nstringhe nuove: {unseen}   (confermate come gia' erano: "
          f"{len(fresh_ones) - unseen})")
    print(f"chiavi che non combaciano con nessuna stringa del gioco: {len(orphans)}")
    for name, en in orphans[:6]:
        print(f"    [{name}] {en[:90]!r}")
    print(f"collisioni fra agenti: {len(collisions)}")
    for a, b, en, x, y in collisions[:6]:
        print(f"    {en[:60]!r}\n       {a}: {x[:70]!r}\n       {b}: {y[:70]!r}")
    print(f"tentativi di riscrivere stringhe gia' fissate: {len(rewrites)}")
    for name, en, old, fresh in rewrites[:6]:
        print(f"    [{name}] {en[:60]!r}\n       tenuta:  {old[:70]!r}\n       scartata:{fresh[:70]!r}")

    doubts = []
    for p in sorted(glob.glob(os.path.join(PARTS, "dubbi_*.json"))):
        try:
            doubts += json.load(open(p, encoding="utf-8"))
        except Exception:
            pass
    print(f"\nstringhe segnalate come dubbie dagli agenti: {len(doubts)}")
    for x in doubts[:20]:
        if isinstance(x, dict):
            print(f"    {x.get('en','?')[:50]!r} -> {x.get('ipotesi','?')[:40]!r}  ({x.get('dubbio','')[:70]})")

    if not dry:
        d["strings"].update(fresh_ones)
        json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
        print(f"\ndizionario: {len(d['strings'])} stringhe")
    else:
        print("\n(dry run: dizionario non modificato)")

if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
