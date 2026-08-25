"""Copertura e integrita': IT vs ES vs CORE.

Conta i *campi dei file del mod* rispetto al core inglese: dice se per ogni
campo del gioco esiste una riga nei file loc. Non dice se quella riga sia
tradotta - una resa identica all'inglese conta come presente, ed e' per questo
che c'e' la colonna "identiche all'inglese". Per dividerle fra volute e buchi:
tools/identical.py. Per il lavoro che resta da fare sul dizionario:
tools/progress.py, che conta un'altra cosa ancora (le voci di it.json).
"""
import collections, sys
from bohloc import *

core, cfiles, cerr, cdup = load_tree(CORE)
print(f"CORE   : {len(core)} entita', {len(cfiles)} file, {len(cerr)} errori parse, {len(cdup)} id duplicati")
for rel, e in cerr[:5]: print("   parse err:", rel, e)

core_strings = sum(len(v["strings"]) for v in core.values())
core_words = sum(len(t.split()) for v in core.values() for t in v["strings"].values())
print(f"         {core_strings} stringhe traducibili, {core_words} parole\n")

def report(name, root):
    idx, files, err, dup = load_tree(root)
    hit = miss = same = empty = 0
    orphan_ids = []
    orphan_fields = 0
    behaviour_leak = collections.Counter()
    covered_words = 0
    missing_by_cat = collections.Counter()
    total_by_cat = collections.Counter()
    for key, cv in core.items():
        cat = key[0]
        lv = idx.get(key)
        for f, ctext in cv["strings"].items():
            total_by_cat[cat] += 1
            if lv is None or f not in lv["strings"]:
                miss += 1; missing_by_cat[cat] += 1; continue
            t = lv["strings"][f]
            if not t.strip():
                empty += 1; missing_by_cat[cat] += 1; continue
            if t.strip() == ctext.strip():
                same += 1
            hit += 1
            covered_words += len(ctext.split())
    for key, lv in idx.items():
        if key not in core:
            orphan_ids.append((key, lv["file"]))
        else:
            for f in lv["strings"]:
                if f not in core[key]["strings"]:
                    orphan_fields += 1
        for k in lv["keys"] & BEHAVIOUR:
            behaviour_leak[k] += 1
    tot = core_strings
    print(f"=== {name} ===")
    print(f"  file: {len(files)}  entita': {len(idx)}  errori parse: {len(err)}  id duplicati nel mod: {len(dup)}")
    print(f"  copertura: {hit}/{tot} stringhe ({100*hit/tot:.1f}%)  ~{covered_words}/{core_words} parole ({100*covered_words/core_words:.1f}%)")
    print(f"  mancanti: {miss}   vuote: {empty}   identiche all'inglese: {same}")
    print(f"      (mancanti = campi assenti dai file; vuote = campi vuoti, che nel core sono")
    print(f"       vuoti anche in inglese; identiche = presenti ma ferme sull'inglese ->")
    print(f"       tools/identical.py le divide fra scelte e buchi)")
    print(f"  id presenti nel mod ma non nel core (orfani): {len(orphan_ids)}")
    print(f"  campi presenti nel mod ma non nel core: {orphan_fields}")
    if behaviour_leak:
        print(f"  campi di logica di gioco copiati nel loc (non dovrebbero esserci): {sum(behaviour_leak.values())} occorrenze")
        for k, n in behaviour_leak.most_common(8): print(f"      {k}: {n}")
    print("  mancanti per categoria:")
    for cat in sorted(total_by_cat, key=lambda c: -missing_by_cat[c]):
        if missing_by_cat[cat]:
            print(f"      {cat:14} {missing_by_cat[cat]:6}/{total_by_cat[cat]:6} mancanti ({100*missing_by_cat[cat]/total_by_cat[cat]:.1f}%)")
    for rel, e in err[:5]: print("   parse err:", rel, e)
    print()
    return idx

it = report("ITALIANO (tuo)", IT)
es = report("SPAGNOLO (Mrdynamite v0.0.7)", ES)
fr = report("FRANCESE (riferimento)", FR)
