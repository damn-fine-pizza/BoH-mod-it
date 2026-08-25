"""Campione affiancato CORE / IT / ES per ispezione visiva."""
from bohloc import *
import random

core, *_ = load_tree(CORE)
it, *_ = load_tree(IT)
es, *_ = load_tree(ES)

random.seed(7)
keys = [k for k in core if core[k]["strings"]]
sample = random.sample(keys, 12)
for k in sample:
    print("=" * 80)
    print(f"{k[0]}/{k[1]}   [{core[k]['file']}]")
    for f, ctext in list(core[k]["strings"].items())[:2]:
        i = it.get(k, {}).get("strings", {}).get(f, "<<ASSENTE>>")
        s = es.get(k, {}).get("strings", {}).get(f, "<<ASSENTE>>")
        print(f"  .{f}")
        print(f"    EN: {ctext[:180]}")
        print(f"    IT: {i[:180]}")
        print(f"    ES: {s[:180]}")

# quante stringhe IT differiscono davvero dall'inglese, e quali sono
print("\n" + "=" * 80)
diff = []
for k, cv in core.items():
    for f, ctext in cv["strings"].items():
        t = it.get(k, {}).get("strings", {}).get(f)
        if t and t.strip() and t.strip() != ctext.strip():
            diff.append((k, f, ctext, t))
print(f"Stringhe IT realmente diverse dall'inglese: {len(diff)}")
import collections
bycat = collections.Counter(k[0] for k, f, c, t in diff)
print("  per categoria:", dict(bycat))
for k, f, c, t in diff[:15]:
    print(f"  [{k[0]}/{k[1]}.{f}]\n     EN: {c[:120]}\n     IT: {t[:120]}")
