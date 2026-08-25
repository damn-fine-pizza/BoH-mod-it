"""Estrae le stringhe inglesi ancora da tradurre, in ordine di priorita'.

Le stringhe distinte si traducono una volta sola: la stessa frase inglese
riceve sempre la stessa resa italiana, per costruzione e non per disciplina.

Uso:
    python extract.py                 # stato di avanzamento
    python extract.py <file.json>     # stringhe da tradurre di quel file di core
    python extract.py --cat elements  # tutte quelle di una categoria
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import load_tree, CORE, PROJ

DICT = os.path.join(PROJ, "translations", "it.json")

# ordine di lavoro: prima i termini che tutto il resto cita
PRIORITY = [
    "elements/_aspects.json", "elements/skills.json", "elements/skills_r.json",
    "elements/tomes.json", "elements/", "verbs/", "decks/", "settings/",
    "legacies/", "achievements/", "endings/", "recipes/",
]

def load_dict():
    if os.path.exists(DICT):
        return json.load(open(DICT, encoding="utf-8"))
    return {"strings": {}, "overrides": {}}

def key_of(cat, eid, field):
    return f"{cat}/{eid}.{field}"

def pending(only=None):
    """-> lista di (testo_inglese, [occorrenze]) non ancora tradotte."""
    d = load_dict()
    core, *_ = load_tree(CORE)
    bytext = collections.OrderedDict()
    for (cat, eid), v in sorted(core.items()):
        rel = v["file"].replace(os.sep, "/")
        if only and only not in rel and only != cat:
            continue
        for field, txt in v["strings"].items():
            t = txt.strip()
            if not t:
                continue
            k = key_of(cat, eid, field)
            if k in d["overrides"] or t in d["strings"]:
                continue
            bytext.setdefault(t, []).append((rel, k))
    return bytext

def prio(rel):
    for i, p in enumerate(PRIORITY):
        if rel.startswith(p):
            return i
    return len(PRIORITY)

if __name__ == "__main__":
    args = sys.argv[1:]
    only = None
    if args and args[0] == "--cat":
        only = args[1]
    elif args:
        only = args[0]

    byt = pending(only)
    if not only:
        tot = sum(len(t.split()) for t in byt)
        d = load_dict()
        print(f"da tradurre: {len(byt)} stringhe distinte, ~{tot} parole")
        print(f"gia' tradotte: {len(d['strings'])} stringhe, {len(d['overrides'])} override")
        percat = collections.Counter()
        for t, occ in byt.items():
            percat[occ[0][0].split("/")[0]] += len(t.split())
        print("\nrestano, per file (in ordine di lavoro):")
        per_file = collections.Counter()
        for t, occ in byt.items():
            per_file[occ[0][0]] += len(t.split())
        for rel in sorted(per_file, key=lambda r: (prio(r), -per_file[r]))[:20]:
            print(f"   {rel:52} {per_file[rel]:7} parole")
    else:
        out = [{"en": t, "occorrenze": len(o), "esempio": o[0][1]} for t, o in byt.items()]
        out.sort(key=lambda x: -x["occorrenze"])
        print(json.dumps(out, ensure_ascii=False, indent=1))
