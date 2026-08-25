"""Rigenera i file di loc_it dai file inglesi di core, applicando il dizionario.

I file loc sono sempre ricostruiti da core: cosi' restano allineati anche quando
il gioco viene aggiornato, e un campo non ancora tradotto resta in inglese, che
e' esattamente il comportamento di fallback del gioco.

I file contengono solo `id` e i campi traducibili, come prescrive il kit: «The
localised version need not and should not contain these fields». Che sia sicuro
non e' un atto di fede nella documentazione, e' misurato sulle tre
localizzazioni ufficiali installate col gioco: loc_ru tiene 28.815 campi di
logica e pesa 6,5 MB, ma loc_jp ne ha uno e pesa 3,5 MB, loc_zh-hans zero e pesa
2,4 MB. Due localizzazioni ufficiali su tre li omettono e il gioco si comporta
uguale: se servissero, giapponese e cinese sarebbero rotti. Per l'italiano
questo vale 4,8 MB contro 1,4.

I campi di testo restano invece anche quando la resa coincide con l'inglese.
Ometterli darebbe lo stesso risultato in partita - il gioco ricade sul core - ma
toglierebbe ai controlli il modo di distinguere «non tradotto» da «uguale
apposta»: e' quello che misurano coverage.py e identical.py.

Uso:
    python apply.py               # rigenera tutto
    python apply.py --dry         # dice solo cosa cambierebbe
    python apply.py --with-logic  # come prima: copia integrale del core
"""
import json, os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import read, CORE, MOD, PROJ, TRANSLATABLE

DICT = os.path.join(PROJ, "translations", "it.json")
DEST = os.path.join(MOD, "loc", "loc_it")

def load_dict():
    if os.path.exists(DICT):
        return json.load(open(DICT, encoding="utf-8"))
    return {"strings": {}, "overrides": {}}

def translate_entity(ent, cat, d, stats):
    """Sostituisce i campi traducibili dell'entita', in loco."""
    eid = ent.get("id") or ent.get("ID")
    if not isinstance(eid, str):
        return
    def pick(field, txt):
        k = f"{cat}/{eid.lower()}.{field}"
        if k in d["overrides"]:
            stats["override"] += 1
            return d["overrides"][k]
        t = d["strings"].get(txt.strip())
        if t is not None:
            stats["tradotte"] += 1
            # Il dizionario ha per chiave il testo senza spazi ai bordi, ma quegli
            # spazi sono struttura: un '\n' iniziale manda a capo, e rimettere la
            # resa nuda lo faceva sparire dal file. Si riattaccano com'erano.
            head = txt[:len(txt) - len(txt.lstrip())]
            tail = txt[len(txt.rstrip()):]
            return head + t + tail if (head or tail) else t
        stats["non_tradotte"] += 1
        return None
    for k in list(ent.keys()):
        kl, v = k.lower(), ent[k]
        if kl in TRANSLATABLE and isinstance(v, str):
            n = pick(kl, v)
            if n is not None:
                ent[k] = n
        elif kl == "xexts" and isinstance(v, dict):
            for xk, xv in list(v.items()):
                if isinstance(xv, str):
                    n = pick(f"xexts.{xk}", xv)
                    if n is not None:
                        v[xk] = n
        elif kl == "slot" and isinstance(v, dict):
            sid = v.get("id", "")
            for sk in list(v.keys()):
                if sk.lower() in TRANSLATABLE and isinstance(v[sk], str):
                    n = pick(f"slot.{sid}.{sk.lower()}", v[sk])
                    if n is not None:
                        v[sk] = n
        elif kl in ("slots", "preslots") and isinstance(v, list):
            for i, s in enumerate(v):
                if not isinstance(s, dict):
                    continue
                sid = s.get("id", i)
                for sk in list(s.keys()):
                    if sk.lower() in TRANSLATABLE and isinstance(s[sk], str):
                        n = pick(f"{kl}.{sid}.{sk.lower()}", s[sk])
                        if n is not None:
                            s[sk] = n

def prune(ent, cat):
    """L'entita' ridotta a cio' che il kit ammette nei file loc.

    Restano l'id, i campi traducibili, gli xext (dove la chiave e' un id e il
    valore e' testo) e gli slot ridotti a id + label + description, che e' la
    forma che il kit mostra. Tutto il resto - reqs, aspects, effects, xtriggers,
    warmup, inherits... - e' logica di gioco che nel file loc non serve.
    """
    outside = {}
    for k, v in ent.items():
        kl = k.lower()
        if kl == "id":
            outside[k] = v
        elif kl in TRANSLATABLE and isinstance(v, str):
            outside[k] = v
        elif kl == "xexts" and isinstance(v, dict):
            outside[k] = v
        elif kl == "slot" and isinstance(v, dict):
            kept = {sk: sv for sk, sv in v.items()
                      if sk.lower() == "id" or (sk.lower() in TRANSLATABLE
                                                and isinstance(sv, str))}
            if kept:
                outside[k] = kept
        elif kl in ("slots", "preslots") and isinstance(v, list):
            slot = []
            for s in v:
                if not isinstance(s, dict):
                    continue
                kept = {sk: sv for sk, sv in s.items()
                          if sk.lower() == "id" or (sk.lower() in TRANSLATABLE
                                                    and isinstance(sv, str))}
                if kept:
                    slot.append(kept)
            if slot:
                outside[k] = slot
    return outside


def main(dry=False, with_logic=False):
    d = load_dict()
    stats = {"tradotte": 0, "non_tradotte": 0, "override": 0, "file": 0}
    for dirpath, _, files in os.walk(CORE):
        rel_dir = os.path.relpath(dirpath, CORE)
        cat = rel_dir.split(os.sep)[0]
        if cat in (".", "cultures", "dicta"):      # loc_ru non ha ne' cultures ne' dicta
            continue
        for fn in sorted(files):
            if not fn.endswith(".json") or "_legacy_" in fn:
                continue
            src = os.path.join(dirpath, fn)
            data = read(src)
            if not isinstance(data, dict):
                continue
            for etype, lst in data.items():
                if not isinstance(lst, list):
                    continue
                for i, ent in enumerate(lst):
                    if not isinstance(ent, dict):
                        continue
                    translate_entity(ent, cat, d, stats)
                    if not with_logic:
                        lst[i] = prune(ent, cat)
            dst = os.path.join(DEST, rel_dir, fn)
            if not dry:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=1)
            stats["file"] += 1
    tot = stats["tradotte"] + stats["non_tradotte"] + stats["override"]
    print(f"file: {stats['file']}")
    print(f"campi tradotti: {stats['tradotte'] + stats['override']}/{tot} "
          f"({100*(stats['tradotte']+stats['override'])/max(1,tot):.1f}%), "
          f"di cui {stats['override']} da override")
    print(f"ancora in inglese: {stats['non_tradotte']}")
    if dry:
        print("(dry run: nessun file scritto)")

if __name__ == "__main__":
    main(dry="--dry" in sys.argv, with_logic="--with-logic" in sys.argv)
