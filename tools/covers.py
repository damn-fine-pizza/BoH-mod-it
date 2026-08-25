"""Scrive le sigle italiane sulle copertine ripulite a mano.

Divisione del lavoro: cancellare la scritta inglese richiede occhio e va fatto a
mano; scriverci sopra quella italiana e' deterministico e lo fa questo script.

Chi ripulisce non deve annotare niente. La posizione della scritta e il suo
colore si ricavano confrontando la lastra ripulita con l'originale: dove i due
file differiscono c'era il testo, e il colore e' quello dei pixel dell'originale
in quel punto. Basta non spostare, non ritagliare e non riscalare.

    art/estratte/en/t.xxx.png originale inglese (copertina), t.xxx_.png (dorso)
    art/lastre/t.xxx.png      la stessa immagine con la scritta cancellata
    mod/BookOfHours_italian/images/books/loc_it/t.xxx.png    il risultato

Il percorso non e' images/books/ ma images/books/loc_it/, ed e' verificato nel
codice del gioco, non dedotto: ResourcesManager.GetSpriteForBookCover(icon)
chiama TryGetSpriteLocalised("books", icon, cultura), che compone
Path.Combine("images", "books", "loc_" + cultura, icon); solo se li' non trova
niente ricade su images/books/. La chiave con cui il mod registra un'immagine e'
il suo percorso relativo alla radice del mod, senza estensione
(ModManager.LoadImage). Scriverle dritte in images/books/ funzionerebbe, ma
sostituirebbe la copertina inglese anche a chi tiene il gioco in inglese col mod
installato. Vedi art/README.md.

Uso:
    python covers.py                 tutte le lastre presenti
    python covers.py t.blacknephrite una sola
    python covers.py --list         cosa manca ancora
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

# Il riferimento dev'essere la stessa sorgente da cui nascono le lastre: gli
# sprite estratti dal gioco. Lo ZIP pubblicato da Weather Factory differisce di
# qualche pixel di antialiasing, abbastanza da falsare il confronto.
ORIG = os.path.join(PROJ, "art", "estratte", "en")
ORIG_ALT = os.path.join(PROJ, "art", "originali")
PLATES = os.path.join(PROJ, "art", "lastre")
FONT = os.path.join(PROJ, "art", "font")
# Le copertine finite si scrivono in un posto solo: il mod, che e' il prodotto ed
# e' dove il gioco legge. La copia in art/italiano/ e' stata tolta perche' era
# identica bit per bit e git se la portava dietro due volte.
DEST_MOD = os.path.join(PROJ, "mod", "BookOfHours_italian", "images", "books", "loc_it")
MANIFEST = os.path.join(PROJ, "art", "manifest.json")
WEIGHTS = {"regular": "EBGaramond-Regular.ttf", "medium": "EBGaramond-Medium.ttf",
        "semibold": "EBGaramond-SemiBold.ttf", "bold": "EBGaramond-Bold.ttf"}


def manifest():
    return {x["id"]: x for x in json.load(open(MANIFEST, encoding="utf-8"))}


def area(orig, plate, threshold=16):
    """-> (riquadro del testo cancellato, suo colore medio nell'originale)"""
    diff = ImageChops.difference(orig, plate).convert("L")
    mask = diff.point(lambda v: 255 if v > threshold else 0)
    bb = mask.getbbox()
    if not bb:
        return None, None
    mp, op = mask.load(), orig.load()
    acc, n = [0, 0, 0], 0
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            if mp[x, y]:
                c = op[x, y]
                for k in range(3):
                    acc[k] += c[k]
                n += 1
    return bb, tuple(a // max(1, n) for a in acc)


def write(img, bb, text, color, weight="semibold", fill=0.92):
    """Scrive la sigla dentro il riquadro, in due corpi come fanno gli originali.

    Sulle copertine inglesi le lettere delle parole funzionali sono piu'
    piccole: GoN ha la o piccola, EfG la f, aCoUP la a e la o. E' la stessa
    distinzione che facciamo noi con maiuscolo e minuscolo, resa pero' con il
    corpo -- e a quella dimensione si legge molto meglio di un cambio di caso.
    Le minuscole si disegnano quindi al 62% e centrate sull'altezza delle
    maiuscole, non appoggiate alla linea di base.

    Un algoritmo solo copre i tre casi che si vedono negli originali: sulla
    copertina la sigla sta su una riga; sul dorso, che e' stretto, le lettere
    si impilano dritte o si spezzano in due righe. Non vanno mai ruotate.
    Il punto mediano separa la sigla dal numero di volume, che va a capo.
    """
    SMALL = 0.62
    x0, y0, x1, y1 = bb
    bw, bh = x1 - x0, y1 - y0
    ttf = os.path.join(FONT, WEIGHTS[weight])

    def font_sizes(dim):
        large = ImageFont.truetype(ttf, dim)
        small = ImageFont.truetype(ttf, max(6, int(round(dim * SMALL))))
        return large, small

    def width_px(line, dim):
        g, p = font_sizes(dim)
        return sum((p if c.islower() else g).getlength(c) for c in line)

    def greedy(piece, dim, limit):
        out, line = [], ""
        for ch in piece:
            if line and width_px(line + ch, dim) > limit:
                out.append(line); line = ch
            else:
                line += ch
        if line:
            out.append(line)
        return out

    def lines_to(dim):
        """Spezza bilanciando, non riempiendo.

        Riempire avidamente la prima riga lascia un avanzo storto: «UTS» sul
        dorso quadrato di Una Torre Sorge diventava UT|S, mentre l'inglese
        spezza ᴀ|TR. Qui invece, fissato il numero minimo di righe che ci stanno
        in larghezza, si cerca la ripartizione che rende piu' stretta la riga
        piu' larga -- che e' come si manda a capo un titolo.
        """
        out = []
        for piece in text.split("·"):
            k = len(greedy(piece, dim, bw * fill))
            if k <= 1:
                out.append(piece)
                continue
            # la larghezza piu' piccola che tiene ancora il testo in k righe
            low = max(width_px(c, dim) for c in piece)
            high = width_px(piece, dim)
            for _ in range(24):
                mid = (low + high) / 2
                if len(greedy(piece, dim, mid)) <= k:
                    high = mid
                else:
                    low = mid
            out += greedy(piece, dim, high)
        return out

    dim, lines = 6, [text]
    for d in range(6, 200):
        r = lines_to(d)
        if max(width_px(x, d) for x in r) > bw * fill:
            break
        g, _ = font_sizes(d)
        top = g.getbbox("H")[3] - g.getbbox("H")[1]
        if len(r) * top + (len(r) - 1) * d * 0.16 > bh * fill:
            break
        dim, lines = d, r

    g, p = font_sizes(dim)
    t_g, b_g = g.getbbox("H")[1], g.getbbox("H")[3]
    top = b_g - t_g
    inter = dim * 0.16
    tot = len(lines) * top + (len(lines) - 1) * inter
    d = ImageDraw.Draw(img)
    y = y0 + (bh - tot) / 2
    for line in lines:
        x = x0 + (bw - width_px(line, dim)) / 2
        for ch in line:
            if ch.islower():
                bb_p = p.getbbox(ch)
                # centrata sull'altezza delle maiuscole, non sulla linea di base
                dy = (top - (bb_p[3] - bb_p[1])) / 2
                d.text((x, y + dy - bb_p[1]), ch, font=p, fill=color)
                x += p.getlength(ch)
            else:
                d.text((x, y - t_g), ch, font=g, fill=color)
                x += g.getlength(ch)
        y += top + inter
    return dim, len(lines)


def one_cover(name, manifest_by_id):
    bid = name[:-1] if name.endswith("_") else name
    entry = manifest_by_id.get(bid)
    if not entry:
        return f"{name}: non e' un libro noto"
    if not entry["sigla"]:
        return f"{name}: manca il titolo italiano, sigla non calcolabile"
    # Il marcatore di volume o anno a volte e' disegnato FUORI dall'area che si
    # cancella -- il 1927 sotto il riquadro sul dorso di Cucurbit Prisoner
    # Records, il ·I· sotto la cornice di Travelling at Night -- e li'
    # sopravvive da solo. Riscriverlo dentro lo raddoppia.
    initials = entry["sigla"]
    suff = "_" if name.endswith("_") else ""
    if suff in entry.get("no_marcatore", []):
        initials = initials.split("·")[0]
    orig_path, plate_path = os.path.join(ORIG, name + ".png"), os.path.join(PLATES, name + ".png")
    if not os.path.exists(orig_path):
        orig_path = os.path.join(ORIG_ALT, name + ".png")
    if not os.path.exists(plate_path):
        return None
    if not os.path.exists(orig_path):
        return f"{name}: manca l'originale"
    orig = Image.open(orig_path).convert("RGB")
    plate = Image.open(plate_path).convert("RGB")
    if orig.size != plate.size:
        return f"{name}: la lastra e' {plate.size}, l'originale {orig.size} — non ritagliare"
    bb, col = area(orig, plate)
    if not bb:
        return f"{name}: la lastra e' identica all'originale, niente da cancellare?"
    out = plate.copy()
    dim, nr = write(out, bb, initials, col, entry.get("peso", "semibold"))
    os.makedirs(DEST_MOD, exist_ok=True)
    out.save(os.path.join(DEST_MOD, name + ".png"))
    return f"{name}: «{initials}» a {dim}px su {nr} riga/he in {bb}, colore {col}"


def main(args):
    manifest_by_id = manifest()
    if "--list" in args:
        ready = {os.path.basename(p)[:-4] for p in os.listdir(PLATES)} if os.path.isdir(PLATES) else set()
        done = {os.path.basename(p)[:-4] for p in os.listdir(DEST_MOD)} if os.path.isdir(DEST_MOD) else set()
        todo = [v for v in manifest_by_id.values() if v["testo"]]
        # un titolo che in italiano resta identico all'inglese - il latino, il
        # lessico inventato, i nomi propri - non ha una copertina da rifare: la
        # sigla inglese e' gia' quella giusta. Segnalarlo come lavoro arretrato
        # ha tenuto aperta per settimane una lista che era chiusa.
        identical = [v for v in todo if (v.get("it") or v["en"]).strip() == v["en"].strip()]
        real_items = [v for v in todo if v not in identical]
        without_plate = [v for v in real_items if v["id"] not in ready]
        without_initials = [v for v in real_items if not v["sigla"]]
        print(f"libri con testo in copertina: {len(todo)}")
        print(f"  gia' scritte nel mod:  {len([v for v in real_items if v['id'] in done])} copertine, "
              f"{len([v for v in real_items if v['id']+'_' in done])} dorsi")
        print(f"  lastre ripulite:       {len([v for v in real_items if v['id'] in ready])} copertine, "
              f"{len([v for v in real_items if v['id']+'_' in ready])} dorsi")
        print(f"  titolo identico all'inglese, copertina gia' buona: {len(identical)}")
        for v in identical:
            print(f"      {v['id']:44} {v['en'][:44]}")
        if without_plate:
            print(f"  DA RIPULIRE (python3 tools/plates.py build <id>): {len(without_plate)}")
            for v in without_plate[:12]:
                print(f"      {v['id']:44} {v['en'][:44]}")
        if without_initials:
            print(f"  senza sigla nel manifest (rilancia initials.py --write): {len(without_initials)}")
            for v in without_initials[:12]:
                print(f"      {v['id']:44} {v['en'][:44]}")
        if not without_plate and not without_initials:
            print("  niente da rifare")
        return
    names = [a for a in args if not a.startswith("--")]
    if not names:
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(PLATES)) if os.path.isdir(PLATES) else []
    done_ones = 0
    for n in names:
        r = one_cover(n, manifest_by_id)
        if r:
            print("  " + r)
            done_ones += not r.count(":") or "«" in r
    print(f"\nscritte: {sum(1 for n in names if os.path.exists(os.path.join(DEST_MOD, n + '.png')))} su {len(names)}")
    print(f"in {os.path.relpath(DEST_MOD, PROJ)}")


if __name__ == "__main__":
    main(sys.argv[1:])
