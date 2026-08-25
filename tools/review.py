"""Prepara il pacchetto da mandare in revisione a un altro modello.

Chi rivede non ha il gioco, non ha il repository e non deve averli: gli serve il
testo, le quattro lingue affiancate e le regole che il progetto si e' dato. Qui
dentro non entra codice, non entra git, non entrano percorsi di questo computer.

Cosa ci va, e perche' proprio questo:

    dizionario/NN.json   il dizionario in slice da 500 voci, e per ogni voce
                         l'inglese, la nostra resa, e quelle di spagnolo e
                         francese dove esistono. Le altre due localizzazioni non
                         sono un'autorita' - sbagliano anche loro - ma sono il
                         modo piu' rapido per accorgersi che una parola era un
                         termine tecnico e non una parola comune.
    interfaccia.json     le label dell'interfaccia, che hanno vincoli di spazio
                         diversi dalla prosa e vanno guardate a parte.
    convenzioni.md       le decisioni gia' prese, con la ragione. Chi rivede
                         deve poterle contestare sapendo che esistono, non
                         riscoprirle una per una.
    glossario.json       i termini vincolanti: sono quelli su cui una
                         segnalazione «e' incoerente» sarebbe gia' stata presa.
    LEGGIMI.md           come e' fatto tutto questo, dentro il pacchetto.

Le slice da 500 servono a chi rivede: un file solo da otto megabyte non entra in
una finestra di contesto, e chi lo riceve lo taglia a caso.

Uso:
    python3 tools/review.py            costruisce dist/review-<versione>.zip
    python3 tools/review.py --parts 300  slice piu' corte
"""
import collections, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, CORE, IT, ES, FR, MOD, load_tree, read

DIST = os.path.join(PROJ, "dist")
DICT = os.path.join(PROJ, "translations", "it.json")
META = os.path.join(PROJ, "translations", "mod.json")
GLOSSARY = os.path.join(PROJ, "translations", "glossario.json")
CONVENTIONS = os.path.join(PROJ, "docs", "convenzioni.md")


def culture(path):
    """Le UI label di un culture.json, se c'e'."""
    try:
        return read(path)["cultures"][0].get("uilabels", {})
    except Exception:
        return {}


def aligned(per_part):
    """-> (voci del dizionario allineate alle quattro lingue, conteggi)"""
    core, *_ = load_tree(CORE)
    it_tree, *_ = load_tree(IT)
    es_tree, *_ = load_tree(ES) if os.path.isdir(ES) else ({},)
    fr_tree, *_ = load_tree(FR) if os.path.isdir(FR) else ({},)
    strings = json.load(open(DICT, encoding="utf-8"))["strings"]

    # dove compare ogni inglese, e come lo rendono gli altri
    where = collections.defaultdict(list)
    other = collections.defaultdict(dict)
    for (cat, eid), v in sorted(core.items()):
        rel = v["file"].replace(os.sep, "/")
        for field, txt in v["strings"].items():
            t = txt.strip()
            if not t:
                continue
            where[t].append(f"{rel}:{eid}.{field}")
            for lang, tree in (("es", es_tree), ("fr", fr_tree)):
                got = tree.get((cat, eid), {}).get("strings", {}).get(field, "").strip()
                if got and lang not in other[t]:
                    other[t][lang] = got

    entries = []
    for en, it in strings.items():
        entries.append({
            "en": en,
            "it": it,
            "es": other.get(en, {}).get("es"),
            "fr": other.get(en, {}).get("fr"),
            "dove": where.get(en, [])[:3],
            "ricorre": len(where.get(en, [])),
        })
    entries.sort(key=lambda x: (-x["ricorre"], x["en"]))
    parts = [entries[i:i + per_part] for i in range(0, len(entries), per_part)]
    return parts, len(entries)


def ui_labels():
    """Le label dell'interfaccia nelle quattro lingue."""
    en = culture(os.path.join(CORE, "cultures", "en", "culture.json"))
    it = culture(os.path.join(MOD, "content", "cultures", "culture.json"))
    es = culture(os.path.join(os.path.dirname(os.path.dirname(ES)),
                              "content", "cultures", "culture.json"))
    fr = {}
    for dirpath, _, filenames in os.walk(FR):
        for fn in filenames:
            if "culture" in fn.lower() and fn.endswith(".json"):
                fr = culture(os.path.join(dirpath, fn)) or fr
    # la copia di riferimento del mod francese non porta il suo culture.json:
    # per le label non c'e' un francese da mettere a fronte, e una colonna di
    # null si legge come un buco della traduzione, che non e'.
    out = []
    for k, v in sorted(en.items()):
        if not it.get(k):
            continue
        voice = {"chiave": k, "en": v, "it": it[k], "es": es.get(k)}
        if fr.get(k):
            voice["fr"] = fr[k]
        out.append(voice)
    return out


LEGGIMI = """# Traduzione italiana di BOOK OF HOURS — materiale per la revisione

Questo pacchetto contiene **solo testo**: nessun codice, nessuna immagine,
nessun file del gioco. Serve a far rileggere la traduzione da fuori.

## Che cosa c'è

| file | contenuto |
|---|---|
| `dizionario/NN.json` | il dizionario in slice da {per_part} voci, ordinate per frequenza: le prime slice contengono le stringhe che si leggono più spesso |
| `interfaccia.json` | le {n_ui} label dell'interfaccia, che hanno vincoli di spazio e vanno guardate a parte. Qui il francese manca: la copia di riferimento del mod francese non porta il suo `culture.json` |
| `convenzioni.md` | le decisioni di traduzione già prese, con la ragione di ciascuna |
| `glossario.json` | i termini vincolanti: resa fissata, non rinegoziabile senza cambiare il glossario |

Ogni voce del dizionario è fatta così:

```json
{{
 "en": "l'originale inglese",
 "it": "la nostra resa",
 "es": "come lo rende il mod spagnolo, se lo rende",
 "fr": "come lo rende il mod francese, se lo rende",
 "dove": ["elements/abilities.json:ability.id.label"],
 "ricorre": 3
}}
```

Spagnolo e francese non sono un'autorità: sbagliano anche loro, e il francese in
più ricopia spesso l'inglese. Servono a capire in fretta se una parola era un
termine tecnico del gioco o una parola comune.

## Numeri

{n_entries} voci distinte, {n_ui} label di interfaccia, {n_parts} slice.
Versione del mod: {version}.
"""


def main(per_part=500):
    os.makedirs(DIST, exist_ok=True)
    version = json.load(open(META, encoding="utf-8"))["version"]
    parts, n_entries = aligned(per_part)
    ui = ui_labels()
    out = os.path.join(DIST, f"review-{version}.zip")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for i, part in enumerate(parts, 1):
            z.writestr(f"dizionario/{i:02d}.json",
                       json.dumps(part, ensure_ascii=False, indent=1))
        z.writestr("interfaccia.json", json.dumps(ui, ensure_ascii=False, indent=1))
        z.writestr("convenzioni.md", open(CONVENTIONS, encoding="utf-8").read())
        z.writestr("glossario.json", open(GLOSSARY, encoding="utf-8").read())
        z.writestr("LEGGIMI.md", LEGGIMI.format(
            per_part=per_part, n_entries=n_entries, n_ui=len(ui),
            n_parts=len(parts), version=version))

    print(f"{os.path.relpath(out, PROJ)}  {os.path.getsize(out)/1024/1024:.1f} MB")
    print(f"  {n_entries} voci in {len(parts)} slice da {per_part}")
    print(f"  {len(ui)} label di interfaccia")
    print(f"  con {sum(1 for p in parts for v in p if v['es'])} rese spagnole "
          f"e {sum(1 for p in parts for v in p if v['fr'])} francesi a fronte")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    n = int(a[a.index("--parts") + 1]) if "--parts" in a else 500
    sys.exit(main(n))
