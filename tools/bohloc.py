"""Loader tollerante per i contenuti JSON di BOOK OF HOURS + estrazione stringhe traducibili."""
import json, json5, os, re, collections

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dove sta il gioco non dipende dal progetto ma da come e' installato - Flatpak,
# Steam nativo, un'altra distribuzione - ed e' l'unica cosa che un altro
# computer debba poter cambiare. Si scrive una volta in percorsi.json, che git
# non segue (si copia percorsi.esempio.json), oppure si passa dall'ambiente:
# BOH_GAME, BOH_MODS, BOH_LOC_ES, BOH_KIT. Se non si dice niente si guarda nei
# posti soliti e si prende il primo che esiste.
_CFG = {}
if os.path.exists(os.path.join(PROJ, "percorsi.json")):
    _CFG = json.load(open(os.path.join(PROJ, "percorsi.json"), encoding="utf-8"))

_STEAM = ("~/.var/app/com.valvesoftware.Steam/.local/share/Steam",   # Flatpak
          "~/.steam/steam", "~/.local/share/Steam")
_UNITY = ("~/.var/app/com.valvesoftware.Steam/.config/unity3d",      # Flatpak
          "~/.config/unity3d")


def path_for(config_key, *candidates):
    """percorsi.json, poi BOH_<CHIAVE> nell'ambiente, poi il primo che esiste."""
    chosen = _CFG.get(config_key) or os.environ.get("BOH_" + config_key.upper())
    if not chosen:
        existing = [c for c in candidates if os.path.exists(os.path.expanduser(c))]
        # se non esiste nessuno si tiene il primo: l'errore lo dara' chi legge,
        # col percorso sotto gli occhi, invece di una stringa vuota.
        chosen = existing[0] if existing else candidates[0]
    return os.path.expanduser(chosen)


GAME = path_for("game", *(f"{s}/steamapps/common/Book of Hours/bh_Data/StreamingAssets/bhcontent"
                          for s in _STEAM))
CORE = os.path.join(GAME, "core")
MOD  = os.path.join(PROJ, "mod", "BookOfHours_italian")   # albero di lavoro
IT   = os.path.join(MOD, "loc", "loc_it")
MODS = path_for("mods", *(f"{u}/Weather Factory/Book of Hours/mods" for u in _UNITY))
IT_INSTALLED = os.path.join(MODS, "BookOfHours_italian", "loc", "loc_it")
# il mod spagnolo, dal Workshop: e' un metro di confronto, non un requisito
ES   = path_for("loc_es", *(f"{s}/steamapps/workshop/content/1028310/3784793429/loc/loc_es"
                            for s in _STEAM))
FR   = os.path.join(MOD, "loc", "_mod_in_french")
# le culture: l'inglese sta nel gioco, la spagnola nel mod scaricato dal
# Workshop, l'italiana nel nostro albero di lavoro.
CULTURE_EN = os.path.join(CORE, "cultures")
CULTURE_ES = os.path.join(os.path.dirname(os.path.dirname(ES)), "content", "cultures", "culture.json")
CULTURE_IT = os.path.join(MOD, "content", "cultures", "culture.json")
# il kit delle immagini localizzabili, che Weather Factory manda a chi lo chiede
KIT = path_for("kit", "~/Downloads/loc_images")

TRANSLATABLE = {"label", "preface", "startdescription", "desc", "description",
                "hint", "descriptionunlocked", "alphalabeloverride"}
# campi che nei file loc NON dovrebbero comparire (sono logica di gioco)
BEHAVIOUR = {"reqs", "effects", "aspects", "mutations", "warmup", "craftable", "actionid",
             "requirements", "linked", "alt", "deckeffects", "purge", "xtriggers", "slots_",
             "inherits", "unique", "uniquenessgroup", "lifetime", "decayto", "icon", "verbicon",
             "audio", "manifestationtype", "resaturate", "burnimage", "achievement", "ambittable",
             "drawmessages", "defaultcard", "spec", "cards", "maxexecutions", "signalimportantloop",
             "portaleffect", "ending", "deleteverb", "haltverb", "fromstack", "internaldeck",
             "isaspect", "noartneeded", "ishidden", "commute", "comments", "image"}

def read(path):
    b = open(path, "rb").read()
    if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raw = b.decode("utf-16")
    else:
        raw = b.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(raw)
    except Exception:
        pass
    try:
        return json5.loads(raw)
    except Exception:
        pass
    # ultima spiaggia: togli trailing commas e ammetti control chars
    cleaned = re.sub(r",(\s*[}\]])", r"\1", raw)
    return json.JSONDecoder(strict=False).decode(cleaned)

def entities(data):
    """Restituisce (tipo_entita, dict) per ogni entita' di primo livello."""
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        out.append((k, e))
    return out

def strings_of(ent):
    """Mappa 'percorso.campo' -> testo, per i campi traducibili di un'entita'."""
    out = {}
    for k, v in ent.items():
        kl = k.lower()
        if kl in TRANSLATABLE and isinstance(v, str):
            out[kl] = v
        elif kl == "xexts" and isinstance(v, dict):
            for xk, xv in v.items():
                if isinstance(xv, str):
                    out[f"xexts.{xk}"] = xv
        elif kl == "slot" and isinstance(v, dict):
            # Il campo si chiama «slot» al singolare in quindici entita' del
            # core - fra cui Consider, Talk e i banchi del villaggio - e per un
            # giro intero nessuno strumento l'ha visto, perche' cercavano solo
            # «slots». Erano 29 stringhe visibili a schermo mai estratte: il
            # bancone dell'Ufficio Postale si leggeva «Post Office Counter».
            sid = v.get("id", "")
            for sk, sv in v.items():
                if sk.lower() in TRANSLATABLE and isinstance(sv, str):
                    out[f"slot.{sid}.{sk.lower()}"] = sv
        elif kl in ("slots", "preslots") and isinstance(v, list):
            # «preslots» sono gli slot che una ricetta mostra prima di partire -
            # Repairs sul Ponte del Cucurbito, Assistance nei saloni - e per un
            # giro intero nessuno strumento li ha visti: 394 stringhe a schermo
            # mai estratte, esattamente come il caso di «slot» singolare.
            for i, s in enumerate(v):
                if isinstance(s, dict):
                    sid = s.get("id", i)
                    for sk, sv in s.items():
                        if sk.lower() in TRANSLATABLE and isinstance(sv, str):
                            out[f"{kl}.{sid}.{sk.lower()}"] = sv
    return out

def load_tree(root, skip_legacy=True):
    """-> {(categoria, id): {'file': relpath, 'strings': {...}, 'keys': set()}}"""
    index, files, errors = {}, [], []
    dupes = []
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith(".json"):
                continue
            if skip_legacy and "_legacy_" in fn:
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            cat = rel.split(os.sep)[0]
            files.append(rel)
            try:
                data = read(p)
            except Exception as e:
                errors.append((rel, str(e)[:100]))
                continue
            for etype, ent in entities(data):
                eid = ent.get("id") or ent.get("ID")
                if not isinstance(eid, str):
                    continue
                key = (cat, eid.lower())
                rec = {"file": rel, "type": etype, "strings": strings_of(ent),
                       "keys": {k.lower() for k in ent.keys()}}
                if key in index:
                    dupes.append((key, index[key]["file"], rel))
                    # unisci: l'ultimo vince ma segnaliamo
                    index[key]["strings"].update(rec["strings"])
                    index[key]["keys"] |= rec["keys"]
                else:
                    index[key] = rec
    return index, files, errors, dupes
