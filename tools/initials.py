"""Ricalcola i titoli italiani e le sigle delle copertine nel manifest.

Le sigle seguono lo schema degli originali inglesi: iniziale maiuscola per le
parole piene, minuscola per le funzionali, articolo iniziale omesso.
Gospel of Nicodemus -> GoN, quindi Vangelo di Nicodemo -> VdN.

Due cose che la prima versione sbagliava.

Il numero di volume. Il dizionario lo tiene fuori dalle parentesi -- "De Horis
book 1 (De Horis), libro 1" -- e prendendo solo cio' che sta dentro le parentesi
i tre volumi diventavano tutti "DH". Ora il marcatore torna nella sigla come lo
mette l'originale: "DH·I".

Le collisioni. Quattro libri diversi rendevano tutti "LdM". Dove due sigle
coincidono si allunga l'ultima parola finche' non si distinguono.

Uso: python initials.py [--write]
"""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

MANIFEST = os.path.join(PROJ, "art", "manifest.json")
DICT = os.path.join(PROJ, "translations", "it.json")
FUNCTION_WORDS = {"di", "del", "dello", "della", "dei", "degli", "delle", "e", "ed", "per", "il", "lo",
        "la", "i", "gli", "le", "un", "uno", "una", "in", "a", "ad", "da", "dal", "dalla",
        "con", "su", "sul", "sulla", "nel", "nella", "che", "al", "alla", "ai", "alle", "d", "l"}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def decompose(value, english):
    """-> (titolo, marcatore di volume o anno, qualificazione)

    La qualificazione e' cio' che distingue i tre «The Three and the Three»,
    quindi entra anche nella sigla. Il numero e l'anno vanno tolti dalla base, o
    finirebbero contati due volte (RdPdC1·1927).

    Le parentesi hanno voluto dire due cose diverse. Nella forma bilingue che il
    progetto ha abbandonato - «The Three and the Three (I Tre e i Tre) -
    Manoscritto di Kerisham» - dentro c'era la traduzione del titolo; nella
    forma attuale, fissata al punto 5-quater delle convenzioni, dentro c'e' la
    qualificazione: «I Tre e i Tre (Manoscritto di Kerisham)». Prendere sempre
    il contenuto delle parentesi come titolo, come faceva la prima versione,
    oggi butta via il titolo e tiene il qualificatore: otto libri diventavano
    «Manoscritto di Kerisham», «Testo di Avignone», «Annotata». Si distinguono
    guardando che cosa sta *prima* della parentesi: se e' il titolo inglese,
    e' la forma vecchia.
    """
    m = re.match(r"^(.*?)\s*\((.+?)\)\s*(.*)$", value)
    if m:
        before, inside, tail = m.groups()
        base_en = re.sub(r"\s*\(.*", "", english).strip().lower()
        if before.strip().lower() == base_en:      # forma bilingue: EN (IT)
            base = inside
        else:                                     # forma attuale: IT (qualificazione)
            base, tail = before, "- " + inside + (" " + tail if tail else "")
    else:
        base, tail = value, ""
    qualifier = ""
    mq = re.match(r"^-\s*(.+?)\s*(?:,\s*(?:vol\.?|libro)\s*\d+)?\s*$", tail)
    if mq:
        qualifier = mq.group(1)
    mark = ""
    mv = re.search(r"(?:vol\.?|libro|book)\s*(\d+)", tail or value, re.I)
    if mv:
        mark = ROMAN.get(int(mv.group(1)), mv.group(1))
    else:
        ma = re.search(r"\b(1[6-9]\d\d|20\d\d)\b", base) or re.search(r"\b(1[6-9]\d\d)\b", english)
        if ma:
            mark = ma.group(1)
    base = re.sub(r",?\s*(?:vol\.?|libro)\s*\d+\s*$", "", base, flags=re.I)
    base = re.sub(r",?\s*\b(?:1[6-9]\d\d|20\d\d)\b", "", base).strip(" ,-")
    return base, mark, qualifier


def initials(t, extra=0):
    """La sigla: una lettera per parola, massimo sei caratteri.

    Il kit ufficiale fissa entrambe le cose. Sulla lunghezza: «short, 1-4
    character titles in the target language». Sullo scopo: «the initials serve
    as a mnemonic device to make it easier to remember which book was which»,
    e «the player doesn't need to be able to parse the title».

    Contribuiscono TUTTE le parole -- maiuscola alle piene, minuscola alle
    funzionali interne, e sempre maiuscola alla prima. «Una Discesa del Guscio»
    da' quindi UDdG, non DG: la forma lunga sta in quattro caratteri e
    distingue molto meglio. E' anche cio' che fa l'inglese, che da A Catalogue
    of Uncharted Pleasures ricava aCoUP.

    Le funzionali si buttano solo quando serve, cioe' quando tenendole si
    sforerebbe il tetto (CAP, sei caratteri: quattro erano troppo pochi perche'
    ora contribuiscono tutte le parole). «Un Catalogo di Piaceri Inesplorati»
    sta in UCdPI e resta cosi'; se sforasse, diventerebbe CPI.
    """
    t = t.strip()
    exclaims = "!" if "!" in t else ("?" if "?" in t else "")
    # l'apostrofo separa due parole: l'Anima -> ["l", "Anima"]
    words = []
    for g in re.split(r"[\s,;:.]+", t):
        for piece in re.split(r"['’]", g):
            w = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", piece)
            if w:
                words.append(w)
    if not words:
        return ""
    full_ones = [w for w in words if w.lower() not in FUNCTION_WORDS] or words

    def build_text(listing, mark_function_words):
        # la prima lettera e' sempre maiuscola, anche se e' un articolo: una
        # sigla che comincia minuscola sta male. «Una Discesa del Guscio» da'
        # quindi UDdG, non uDdG.
        out = []
        for k, w in enumerate(listing):
            lowercase = mark_function_words and w.lower() in FUNCTION_WORDS and k > 0
            out.append(w[0].lower() if lowercase else w[0].upper())
        if extra:
            # per sciogliere una collisione si aggiunge la prima lettera che
            # distingue, non lettere consecutive
            w = listing[-1]
            if extra < len(w):
                out[-1] += w[extra].lower()
        return "".join(out)

    # Il kit chiede 1-4 caratteri, ma le poche sigle che ne prendono cinque o
    # sei distinguono molto meglio di una troncata, e restano leggibili: si
    # tiene la forma lunga fino a sei. Oltre, si buttano le funzionali.
    CAP = 6
    more = 1 if extra else 0
    long = build_text(words, True)
    if len(long) <= CAP + more:
        return long + exclaims
    short = build_text(full_ones, False)
    return short[:CAP + more] + exclaims


def last_word(t):
    """L'ultima parola piena del titolo: e' quella su cui cade la sigla."""
    words = []
    for g in re.split(r"[\s,;:.]+", t):
        for piece in re.split(r"['’]", g):
            w = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", piece)
            if w and w.lower() not in FUNCTION_WORDS:
                words.append(w)
    return words[-1] if words else ""


def main(write=False):
    manifest_by_id = json.load(open(MANIFEST, encoding="utf-8"))
    d = json.load(open(DICT, encoding="utf-8"))["strings"]
    for x in manifest_by_id:
        v = d.get(x["en"])
        if v is None:
            x["stato"] = "non tradotto"; x["it"] = ""; x["sigla"] = ""; continue
        if v.strip() == x["en"].strip():
            x["stato"] = "invariato"; x["it"] = v; x["sigla"] = ""; continue
        base, mark, qualifier = decompose(v, x["en"])
        x["stato"] = "tradotto"
        x["it"] = base + (f" - {qualifier}" if qualifier else "") + (f", {mark}" if mark else "")
        x["_base"] = base; x["_marc"] = mark; x["_qual"] = qualifier

    # collisioni: si allunga l'ultima parola finche' le sigle si distinguono
    for round_ in range(5):
        for x in manifest_by_id:
            if x.get("stato") == "tradotto":
                q = initials(x["_qual"])[:2 + x.get("_extra", 0)] if x["_qual"] else ""
                x["sigla"] = initials(x["_base"], x.get("_extra", 0)) + \
                             (("·" + q) if q else "") + \
                             (("·" + x["_marc"]) if x["_marc"] else "")
        # Si guarda la sigla COMPLETA, marcatore incluso. Volumi ed edizioni
        # della stessa opera devono condividere la base e distinguersi solo per
        # il marcatore -- De Horis I, II, III sono lo stesso libro in tre tomi --
        # e a separarli sul serio c'e' comunque l'illustrazione, che e' diversa
        # per ogni carta. Disambiguare sulla base spezzava proprio quei gruppi.
        def base(x):
            return x["sigla"]
        c = collections.Counter(base(x) for x in manifest_by_id if x.get("stato") == "tradotto")
        dup = {s for s, n in c.items() if n > 1}
        if not dup:
            break
        # per ogni gruppo che collide, l'indice della prima lettera in cui le
        # parole distintive si differenziano
        for ini in dup:
            group = [x for x in manifest_by_id if x.get("stato") == "tradotto" and base(x) == ini]
            code = []
            for x in group:
                pa = last_word(x["_base"])
                code.append(pa)
            n = min((len(w) for w in code), default=0)
            pos = next((i for i in range(1, n) if len({w[i].lower() for w in code}) > 1), None)
            for x in group:
                x["_extra"] = pos if pos is not None else x.get("_extra", 0) + 1
        for x in []:
            # oltre tre lettere in piu' la sigla smette di essere una sigla:
            # meglio due libri che la condividono, come capita anche in inglese.
            # Tre e non due perche' «Il Tantra Incessante» e «Il Tantra
            # Incandescente» cominciano entrambi per Inc: servono Ince e Inca.
            pass
    for x in manifest_by_id:
        for k in ("_base", "_marc", "_qual", "_extra"): x.pop(k, None)

    books = [x for x in manifest_by_id if x["testo"] and x["stato"] == "tradotto"]
    c = collections.Counter(x["sigla"] for x in books)
    dup = [(s, n) for s, n in c.items() if n > 1]
    print(f"libri da rifare: {len(books)}")
    print(f"sigle ancora duplicate: {len(dup)} {dup[:5]}")
    print("lunghezze:", dict(sorted(collections.Counter(len(x['sigla']) for x in books).items())))
    print("\nesempi con volume o anno:")
    for x in books:
        if "·" in x["sigla"]:
            print(f"   {x['en'][:40]:40} -> {x['it'][:36]:36} {x['sigla']}")
    if write:
        json.dump(manifest_by_id, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\nmanifest aggiornato")


def check_one():
    """Controlla che ogni sigla sia davvero derivabile dal suo titolo.

    Il difetto che ha motivato questo controllo: «l'Anima» veniva spezzata
    sull'apostrofo e la parola vera spariva dalla sigla, in silenzio. Qui si
    conta: tante lettere quante parole, maiuscole sulle piene, minuscole sulle
    funzionali. Cio' che non torna viene elencato.
    """
    manifest_by_id = json.load(open(MANIFEST, encoding="utf-8"))
    books = [x for x in manifest_by_id if x["testo"] and x["stato"] == "tradotto"]
    lost, mismatched, cut_ones = [], [], []
    for x in books:
        base = re.sub(r"\s*-\s*.*$", "", x["it"])
        base = re.sub(r",\s*(?:[IVX]+|1[6-9]\d\d|20\d\d)\s*$", "", base)
        words = [w for g in re.split(r"[\s,;:.]+", base)
                  for w in re.split(r"['’]", g) if re.search(r"[A-Za-zÀ-ÿ0-9]", w)]
        expected_value = initials(base)
        font_size = x["sigla"].split("·")[0].rstrip("!?")
        # Non si conta "una lettera per parola": sopra le sei il tetto butta di
        # proposito le funzionali. Si confronta con la derivazione attesa.
        full_ones = [w for w in words if re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", w).lower() not in FUNCTION_WORDS]
        if len(font_size) < min(len(full_ones), 4):
            lost.append((x, words, font_size))
        if not font_size.startswith(expected_value.rstrip("!?")[:len(font_size)]):
            mismatched.append((x, expected_value, font_size))
        if len(full_ones) > 4:
            cut_ones.append((x, len(words), font_size))
    c = collections.Counter(x["sigla"] for x in books)
    dup = sorted([(s, n) for s, n in c.items() if n > 1], key=lambda t: -t[1])

    print(f"libri verificati: {len(books)}")
    print(f"  parole perse nella sigla:      {len(lost)}")
    for x, pa, co in lost[:10]:
        print(f"     {x['it'][:44]:46} {co:8} ({len(pa)} parole: {' '.join(pa)[:44]})")
    print(f"  sigla non derivabile dal titolo: {len(mismatched)}")
    for x, at, co in mismatched[:10]:
        print(f"     {x['it'][:44]:46} ha {co!r}, atteso {at!r}")
    print(f"  titoli con piu' di 4 parole piene (sigla troncata di proposito): {len(cut_ones)}")
    for x, n, co in cut_ones[:6]:
        print(f"     {x['it'][:52]:54} {n} parole -> {co}")
    print(f"  sigle duplicate: {len(dup)} {dup[:6]}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check_one()
    else:
        main("--write" in sys.argv)
