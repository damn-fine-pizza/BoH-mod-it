"""Ricava automaticamente le copertine ripulite dalla scritta inglese.

Nessun intervento a mano. L'idea sta in una asimmetria fra le tre localizzazioni
ufficiali: il russo tiene il layout della copertina e cambia solo le lettere,
mentre giapponese e cinese rimpaginano. Quindi

 1. EN contro RU dice DOVE sta il testo, e solo il testo: quello che resta
    uguale e' illustrazione e non va toccato (il pentagramma di Exorcism for
    Girls, che un confronto con jp o zh avrebbe cancellato);
 2. dentro quel riquadro, per ogni pixel si sceglie fra le quattro lingue il
    valore piu' vicino al colore del pannello: dove una lingua ha inchiostro,
    un'altra quasi sempre ha pannello pulito;
 3. una passata finale toglie i residui, cioe' i pochi pixel dove tutte e
    quattro hanno inchiostro nello stesso punto.

I libri con copertina puramente pittorica si riconoscono da soli: se EN e RU
sono identici non c'e' testo, e l'immagine resta intatta.

Le quattro versioni stanno dentro resources.assets, indirizzate dal
ResourceManager come images/books/[loc_<cultura>/]t.<id>. Servono UnityPy e
Pillow: usare il venv del progetto (.venv).

Uso:
    python plates.py extract    tira fuori le quattro versioni (una volta sola)
    python plates.py build      costruisce art/plates/
    python plates.py build t.blacknephrite
    python plates.py survey     quante lastre hanno ancora macchie
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, CORE

GAME = os.path.dirname(os.path.dirname(CORE))          # .../bh_Data/StreamingAssets/..
BHDATA = os.path.join(os.path.dirname(os.path.dirname(GAME)), "bh_Data") \
    if "bh_Data" not in GAME else GAME
ART = os.path.join(PROJ, "art")
EXTRACTED = os.path.join(ART, "estratte")
PLATES = os.path.join(ART, "plates")
CULTURES = ("en", "ru", "jp", "zh-hans")


def _bhdata():
    p = CORE
    while p and os.path.basename(p) != "bh_Data":
        fresh_one = os.path.dirname(p)
        if fresh_one == p:
            raise SystemExit("non trovo bh_Data a partire da " + CORE)
        p = fresh_one
    return p


def extract():
    import UnityPy
    bh = _bhdata()
    env = UnityPy.load(os.path.join(bh, "globalgamemanagers"))
    rm = [o for o in env.objects if o.type.name == "ResourceManager"][0].read_typetree()
    external = {i + 1: e.path for i, e in enumerate(list(env.files.values())[0].externals)}
    intended_ids = collections.defaultdict(dict)          # file -> {path_id: destinazione}
    for path_for, ptr in rm["m_Container"]:
        if not path_for.startswith("images/books/"):
            continue
        rest = path_for[len("images/books/"):]
        cul = "en"
        if rest.startswith("loc_"):
            cul, _, rest = rest.partition("/")
            cul = cul[4:]
        if not rest.startswith("t."):
            continue
        f = external.get(ptr["m_FileID"])
        if not f:
            continue
        intended_ids[os.path.basename(f)][ptr["m_PathID"]] = (cul, rest)
    for cul in CULTURES:
        os.makedirs(os.path.join(EXTRACTED, cul), exist_ok=True)
    written = skipped_ids = 0
    for filename, mapping in intended_ids.items():
        p = os.path.join(bh, filename)
        if not os.path.exists(p):
            print(f"  {filename}: assente, salto {len(mapping)} sprite"); continue
        e2 = UnityPy.load(p)
        for o in e2.objects:
            if o.path_id not in mapping:
                continue
            cul, name = mapping[o.path_id]
            dest = os.path.join(EXTRACTED, cul, name + ".png")
            if os.path.exists(dest):
                skipped_ids += 1; continue
            try:
                img = o.read().image
            except Exception:
                continue
            img.convert("RGBA").save(dest); written += 1
        print(f"  {filename}: {written} scritte, {skipped_ids} gia' presenti")
    for cul in CULTURES:
        d = os.path.join(EXTRACTED, cul)
        print(f"  {cul}: {len(os.listdir(d))} immagini")


def _align(en, im):
    """Riporta una versione localizzata alle dimensioni dell'inglese.

    Tre libri - I Libri di Ferro, d'Avorio e d'Argento - hanno lo sprite inglese
    di quattro pixel piu' alto delle altre culture: il confronto veniva saltato
    e la copertina passava per pittorica, cioe' senza testo, mentre il testo
    c'era (I B, Ж К). Si cerca lo scarto che minimizza la differenza - per
    quei tre e' due pixel, cioe' sono centrate - e il bordo scoperto si riempie
    con l'inglese stesso, cosi' non produce differenze finte.
    """
    import numpy as np
    from PIL import Image
    if im.size == en.size:
        return im
    a = np.asarray(en, dtype=np.int16)
    b = np.asarray(im, dtype=np.int16)
    if b.shape[0] > a.shape[0] or b.shape[1] > a.shape[1]:
        return None                       # piu' grande dell'inglese: non e' lo stesso disegno
    dy = a.shape[0] - b.shape[0]
    dx = a.shape[1] - b.shape[1]
    best, off = None, (0, 0)
    for y in range(dy + 1):
        for x in range(dx + 1):
            d = np.abs(a[y:y + b.shape[0], x:x + b.shape[1]] - b).mean()
            if best is None or d < best:
                best, off = d, (y, x)
    merged_one = a.copy()
    merged_one[off[0]:off[0] + b.shape[0], off[1]:off[1] + b.shape[1]] = b
    return Image.fromarray(merged_one.astype("uint8"), "RGB")


def _load(name):
    from PIL import Image
    out = {}
    for c in CULTURES:
        p = os.path.join(EXTRACTED, c, name + ".png")
        if os.path.exists(p):
            out[c] = Image.open(p).convert("RGB")
    en = out.get("en")
    if en is not None:
        for c in list(out):
            if c == "en":
                continue
            aligned = _align(en, out[c])
            if aligned is None:
                del out[c]
            else:
                out[c] = aligned
    return out


def text_box(ims, threshold=34):
    """Dove sta il testo. Il russo per primo: tiene il layout."""
    from PIL import ImageChops
    en = ims.get("en")
    if en is None:
        return None
    for c in ("ru", "jp", "zh-hans"):
        i = ims.get(c)
        if i is None or i.size != en.size:
            continue
        bb = ImageChops.difference(en, i).convert("L") \
             .point(lambda v: 255 if v > threshold else 0).getbbox()
        if bb:
            return bb
    return None


def plate(ims, bb, margin=2, radius=3, dither=True):
    """Cancella la scritta senza toccare il resto.

    Due passaggi, e il secondo e' deliberatamente timido.

    Il primo sfrutta il fatto che l'illustrazione e' identica in tutte e quattro
    le lingue mentre il testo no: si modificano solo i pixel dove le quattro
    versioni discordano, e per ognuno si prende il valore piu' vicino al colore
    del pannello -- dove una lingua ha inchiostro, un'altra di solito ha
    pannello pulito. Ovali, cornici e grana restano identici al pixel, perche'
    non vengono nemmeno letti.

    Restano pero' delle macchioline: i punti in cui tutte e quattro le lingue
    hanno inchiostro, dove il disaccordo non vede niente. Il secondo passaggio
    le cerca e lavora solo su quelle. La garanzia sta nel limite di dimensione:
    si toccano solo i grumi piccoli, quindi una cornice o un ovale -- che sono
    grandi e connessi -- non possono mai finire dentro.
    """
    import numpy as np
    from PIL import Image, ImageFilter
    en = ims["en"]
    W, H = en.size
    x0 = max(0, bb[0] - margin); y0 = max(0, bb[1] - margin)
    x1 = min(W, bb[2] + margin); y1 = min(H, bb[3] + margin)

    A = np.stack([np.asarray(i, dtype=np.int16) for i in ims.values() if i.size == en.size])
    base = np.asarray(en, dtype=np.int16).copy()
    box = np.zeros((H, W), bool); box[y0:y1, x0:x1] = True

    def grow(m, n=1):
        for _ in range(n):
            d = m.copy()
            d[1:] |= m[:-1]; d[:-1] |= m[1:]
            d[:, 1:] |= m[:, :-1]; d[:, :-1] |= m[:, 1:]
            m = d & box
        return m

    def spread(img, to_fill, rounds=200):
        """Riempie una maschera dai vicini gia' buoni. Non tocca nient'altro."""
        res = to_fill.copy()
        for _ in range(rounds):
            if not res.any():
                break
            good_ones = ~res
            total = np.zeros((H, W, 3), np.float64); count = np.zeros((H, W), np.float64)
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                v = np.roll(np.roll(img, dy, axis=0), dx, axis=1).astype(np.float64)
                m = np.roll(np.roll(good_ones, dy, axis=0), dx, axis=1)
                total += v * m[:, :, None]; count += m
            full_items = res & (count > 0)
            if not full_items.any():
                break
            img[full_items] = (total[full_items] / count[full_items][:, None]).round().astype(np.int16)
            res &= ~full_items
        return img

    # 1. dove le lingue discordano c'e' il testo, e solo quello.
    #    Attenzione alla precedenza: in Python & lega piu' forte di >, e senza le
    #    parentesi "> 26 & box" diventava "> 0", cioe' ogni pixel con una
    #    qualunque differenza -- antialiasing compreso -- finiva fra il testo.
    disc = grow(((A.max(axis=0) - A.min(axis=0)).max(axis=2) > 26) & box, 2)

    # 2. L'unione di tutte le aree di testo, allargata di un raggio. I contorni
    #    di ogni lettera stanno sempre in disc, perche' i glifi hanno forme
    #    diverse in ogni lingua; il cuore di un tratto dista dal contorno al piu'
    #    meta' larghezza di tratto, quindi un raggio piccolo lo assorbe. Non
    #    serve ne' soglia ne' topologia.
    # Il raggio serve a coprire il cuore dei tratti, ma cosi' inghiotte anche
    # l'illustrazione che sta DENTRO l'area di testo -- il cerchio sottile
    # dietro il titolo di The Known-Unknown Tantra, per esempio. Quel cerchio
    # e' identico in tutte e quattro le lingue, quindi e' disegno.
    # Si riempie percio' solo cio' che e' conteso oppure chiaramente inchiostro:
    # i pixel su cui le lingue concordano e che sono vicini al colore del
    # pannello sono illustrazione, e restano.
    inside = box & ~disc
    panel = np.median(base[inside], axis=0) if inside.sum() >= 30 else np.median(base.reshape(-1, 3), axis=0)
    agreeing = (A.max(axis=0) - A.min(axis=0)).max(axis=2) <= 26
    light = np.abs(base - panel[None, None, :]).max(axis=2) < 60
    area = grow(disc, radius) & ~(agreeing & light)
    area |= disc                       # il conteso si riempie sempre

    # 3. Si riempie SPAZIALMENTE, dal pannello attorno. Non si prende un solo
    #    pixel da un'altra lingua: su copertine come The Sky, The Soul tutte e
    #    quattro coprono la stessa area centrale, quel pannello non e' mai stato
    #    visto libero in nessuna versione, e "la lingua piu' vicina al pannello"
    #    finiva per incollare glifi cinesi.
    #    Il riempimento e' in due tempi, e non usa mai colori inventati.
    #    Prima un fondo liscio per diffusione dal bordo della zona; poi, al
    #    punto 5, la grana e la struttura vere copiate da altrove.
    #    Non si campiona a caso: su un pannello piatto il rumore casuale
    #    lascia una chiazza di puntini ben visibile. Non si fa dithering:
    #    aggiunge struttura dove non ce n'e'.
    out = spread(base.copy(), area)
    holes = area

    # 5. La diffusione spalma: dove il pannello ha un disegno -- i gigli di
    #    Wainscot Histories, la striscia diagonale di On the Winding Stair --
    #    lo perde. Si cerca allora nell'immagine stessa la traslazione il cui
    #    contorno combacia meglio, e si riportano quei pixel: una toppa che
    #    continua il disegno invece di stenderlo.
    #
    #    La toppa va cercata PER SINGOLA LETTERA, non per tutto il blocco di
    #    testo: una toppa sola grande quanto il titolo copia anche i gradienti
    #    e lascia una cucitura visibile a X.
    for comp in components(area):
        cy, cx = comp
        by0, by1, bx0, bx1 = cy.min(), cy.max(), cx.min(), cx.max()
        m = 5
        ry0, ry1 = max(0, by0 - m), min(H, by1 + 1 + m)
        rx0, rx1 = max(0, bx0 - m), min(W, bx1 + 1 + m)
        th, tw = ry1 - ry0, rx1 - rx0
        target = base[ry0:ry1, rx0:rx1].astype(np.float32)
        val_b = ~area[ry0:ry1, rx0:rx1]
        if val_b.sum() < 12:
            continue
        better, score = None, None
        for dy in range(-40, 41):
            for dx in range(-40, 41):
                if abs(dy) + abs(dx) < 2:
                    continue
                sy, sx = ry0 + dy, rx0 + dx
                if sy < 0 or sx < 0 or sy + th > H or sx + tw > W:
                    continue
                val_s = ~area[sy:sy + th, sx:sx + tw]
                ok = val_b & val_s
                if ok.sum() < 0.6 * val_b.sum():
                    continue
                src_dir = base[sy:sy + th, sx:sx + tw].astype(np.float32)
                sc = float((((target - src_dir) ** 2).sum(axis=2))[ok].mean())
                if score is None or sc < score:
                    score, better = sc, (dy, dx)
        if better is None or score > 700:
            continue
        dy, dx = better
        inside = (cy + dy >= 0) & (cy + dy < H) & (cx + dx >= 0) & (cx + dx < W)
        sy, sx = cy[inside] + dy, cx[inside] + dx
        free = ~area[sy, sx]
        out[cy[inside][free], cx[inside][free]] = base[sy[free], sx[free]]
    # 6. Resta il difetto della diffusione: riempiendo da quattro lati produce
    #    un gradiente liscio a X, che su un pannello granuloso si vede subito.
    #    Si quantizza allora l'area con la PALETTE DEL FONDO -- i colori che il
    #    pannello usa davvero attorno al buco, senza quelli delle lettere --
    #    diffondendo l'errore alla Floyd-Steinberg. Il gradiente sparisce nel
    #    rumore, e il rumore e' quello giusto perche' i colori sono quelli.
    ring = area.copy()
    for _ in range(8):
        d = ring.copy()
        d[1:] |= ring[:-1]; d[:-1] |= ring[1:]
        d[:, 1:] |= ring[:, :-1]; d[:, :-1] |= ring[:, 1:]
        ring = d
    ring &= ~area
    if False and ring.sum() >= 40 and area.any():
        sample = base[ring]
        center = np.median(out[area], axis=0)
        # via i colori delle lettere: si tiene cio' che assomiglia al fondo
        neighbours = sample[np.abs(sample - center).max(axis=1) < 40]
        if len(neighbours) >= 30:
            colors, count_of = np.unique(neighbours, axis=0, return_counts=True)
            tab = colors[np.argsort(-count_of)[:14]].astype(np.float32)
            books = out.astype(np.float32)
            ys, xs = np.nonzero(area)
            order = np.lexsort((xs, ys))
            for k in order:
                y, x = ys[k], xs[k]
                v = books[y, x]
                i = int(((tab - v) ** 2).sum(axis=1).argmin())
                err = v - tab[i]
                books[y, x] = tab[i]
                for ddy, ddx, w in ((0, 1, 7/16), (1, -1, 3/16), (1, 0, 5/16), (1, 1, 1/16)):
                    ny, nx = y + ddy, x + ddx
                    if 0 <= ny < H and 0 <= nx < W and area[ny, nx]:
                        books[ny, nx] += err * w
            out[area] = np.clip(books[area], 0, 255).astype(np.int16)

    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB")


def components(m):
    """Le componenti connesse di una maschera, come coppie di array (y, x)."""
    import numpy as np
    H, W = m.shape
    seen_one = np.zeros_like(m)
    outside = []
    for sy, sx in zip(*np.nonzero(m)):
        if seen_one[sy, sx]:
            continue
        stack = [(sy, sx)]; seen_one[sy, sx] = True; comp = []
        while stack:
            y, x = stack.pop(); comp.append((y, x))
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen_one[ny, nx]:
                    seen_one[ny, nx] = True; stack.append((ny, nx))
        if len(comp) >= 6:
            outside.append((np.array([c[0] for c in comp]), np.array([c[1] for c in comp])))
    return outside


def stains(name, minimum=8):
    """Censisce l'inchiostro residuo di una lastra, e quanto spazio ha intorno.

    Sono i punti in cui tutte e quattro le lingue avevano inchiostro nello
    stesso pixel: il composito non ha una versione pulita da cui pescare e
    lascia un grumo. Toglierli con una soglia automatica si e' rivelato peggio
    del male, perche' ogni soglia che prendeva i grumi prendeva anche pezzi di
    illustrazione. Qui quindi si misura soltanto.

    Per ogni grumo: area, riquadro, e il raggio entro cui il pannello attorno e'
    uniforme -- cioe' quanto si puo' allargare l'intervento senza toccare altro.

    -> [(area, x0, y0, x1, y1, raggio_libero), ...]
    """
    import numpy as np
    from PIL import Image, ImageFilter
    plate_path = os.path.join(PLATES, name + ".png")
    pe = os.path.join(EXTRACTED, "en", name + ".png")
    if not (os.path.exists(plate_path) and os.path.exists(pe)):
        return []
    l = Image.open(plate_path).convert("RGB")
    a = np.asarray(l, dtype=np.int16)
    b = np.asarray(l.filter(ImageFilter.MedianFilter(9)), dtype=np.int16)
    # il grumo spicca sul proprio intorno; il confronto e' con la lastra stessa,
    # non con l'originale, che li' ha ancora le lettere
    m = np.abs(a - b).max(axis=2) > 24
    # solo dove abbiamo lavorato: fuori dal riquadro ogni contrasto e' disegno
    e = np.asarray(Image.open(pe).convert("RGB"), dtype=np.int16)
    touch = np.abs(a - e).max(axis=2) > 4
    if not touch.any():
        return []
    ys, xs = np.nonzero(touch)
    box = np.zeros(m.shape, bool)
    box[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
    m &= box

    H, W = m.shape
    seen_one = np.zeros_like(m)
    outside = []
    for sy, sx in zip(*np.nonzero(m)):
        if seen_one[sy, sx]:
            continue
        stack = [(sy, sx)]; seen_one[sy, sx] = True; comp = []
        while stack:
            y, x = stack.pop(); comp.append((y, x))
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen_one[ny, nx]:
                    seen_one[ny, nx] = True; stack.append((ny, nx))
        if len(comp) < minimum:
            continue
        yy = [c[0] for c in comp]; xx = [c[1] for c in comp]
        bx0, by0, bx1, by1 = min(xx), min(yy), max(xx), max(yy)
        # Quanto si puo' allargare restando su pannello uniforme. La soglia
        # dev'essere RELATIVA alla grana locale: una soglia fissa la grana del
        # pannello la supera da sola, e il raggio risultava sempre zero.
        grain = float(np.abs(a - b)[max(0, by0-10):by1+11,
                                    max(0, bx0-10):bx1+11].std())
        radius = 0
        for r in range(1, 13):
            ax0, ay0 = max(0, bx0 - r), max(0, by0 - r)
            ax1, ay1 = min(W, bx1 + r + 1), min(H, by1 + r + 1)
            border = a[ay0:ay1, ax0:ax1].reshape(-1, 3)
            center = np.median(border, axis=0)
            if float(np.abs(border - center).mean()) > max(6.0, 2.5 * grain):
                break
            radius = r
        outside.append((len(comp), bx0, by0, bx1, by1, radius))
    return sorted(outside, reverse=True)


def survey():
    """Quante lastre hanno ancora macchie, quanto grandi, con quanto spazio."""
    import collections
    manifest_by_id = {x["id"]: x for x in json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))}
    names = []
    for x in manifest_by_id.values():
        if x["testo"] and x["stato"] != "invariato":
            names += [x["id"], x["id"] + "_"]
    dirty, tot, areas, radii = [], 0, [], []
    for n in sorted(names):
        mm = stains(n)
        if mm:
            dirty.append((n, mm))
            tot += len(mm)
            areas += [m[0] for m in mm]
            radii += [m[5] for m in mm]
    done = [n for n in names if os.path.exists(os.path.join(PLATES, n + ".png"))]
    print(f"lastre prodotte: {len(done)} su {len(names)}")
    print(f"lastre con macchie residue: {len(dirty)}  ({100*len(dirty)/max(1,len(done)):.0f}%)")
    print(f"macchie totali: {tot}")
    if areas:
        areas.sort()
        print(f"area delle macchie in pixel: mediana {areas[len(areas)//2]}, "
              f"90esimo {areas[int(len(areas)*0.9)]}, massima {areas[-1]}")
        print(f"raggio di pannello uniforme attorno: mediana {sorted(radii)[len(radii)//2]}, "
              f"minimo {min(radii)}")
        print("")
        print("le dieci lastre piu' sporche:")
        for n, mm in sorted(dirty, key=lambda t: -sum(x[0] for x in t[1]))[:10]:
            print(f"   {n:46} {len(mm)} macchie, {sum(x[0] for x in mm)} px, "
                  f"la piu' grande {mm[0][0]} px in ({mm[0][1]},{mm[0][2]})-({mm[0][3]},{mm[0][4]}) "
                  f"raggio libero {mm[0][5]}")


def small_components(m, limit):
    """Tiene solo i grumi con meno di `limite` pixel.

    E' la garanzia del secondo passaggio: una cornice o un ovale sono grandi e
    connessi, quindi non possono finire fra le macchie da cancellare.
    """
    import numpy as np
    H, W = m.shape
    seen_one = np.zeros_like(m)
    outside = np.zeros_like(m)
    ys, xs = np.nonzero(m)
    for sy, sx in zip(ys, xs):
        if seen_one[sy, sx]:
            continue
        stack = [(sy, sx)]; seen_one[sy, sx] = True; comp = []
        while stack:
            y, x = stack.pop()
            comp.append((y, x))
            if len(comp) > limit:
                break
            for dy, dx in ((-1,0),(1,0),(0,-1),(0,1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen_one[ny, nx]:
                    seen_one[ny, nx] = True; stack.append((ny, nx))
        if len(comp) <= limit:
            for y, x in comp:
                outside[y, x] = True
    return outside


def redo(names, maximum=9, dither=False):
    """Rifa' una lastra cercando il raggio che le serve, invece di imporne uno.

    Un raggio unico non puo' andare bene per tutte: dove le lettere sono sottili
    ne basta poco e di piu' fa danno -- scambia la grana per inchiostro e lascia
    decine di macchioline -- mentre dove i tratti sono spessi ne serve di piu' o
    sopravvive mezza lettera. Qui il raggio sale finche' la lastra non e' pulita,
    e si ferma appena lo e': si prende sempre il piu' piccolo che basta.

    Il tetto lo da' la misura fatta sul posto: attorno alle macchie ci sono in
    mediana 12 pixel di pannello uniforme, quindi fino a nove si resta larghi.

    Qui il dithering resta spento. Serviva a nascondere il gradiente della
    diffusione, ma il riempimento pesca gia' colori veri del pannello: aggiunto
    sopra, su alcune copertine lasciava un rettangolo di puntini ben visibile --
    che il censimento contava come macchie, quando erano sue.
    """
    from PIL import Image
    results = []
    for bid in names:
        ims = _load(bid)
        if "en" not in ims:
            results.append((bid, None, "manca l'inglese")); continue
        bb = text_box(ims)
        if not bb:
            results.append((bid, None, "nessun testo")); continue
        best_im, best_mm, best_radius = None, None, None
        for r in range(3, maximum + 1, 2):
            im = plate(ims, bb, radius=r, dither=dither)
            im.save(os.path.join(PLATES, bid + ".png"))
            mm = stains(bid)
            rest = sum(m[0] for m in mm)
            if best_im is None or rest < best_mm:
                best_im, best_mm, best_radius = im, rest, r
            if not mm:
                break
        best_im.save(os.path.join(PLATES, bid + ".png"))
        results.append((bid, best_radius, f"{best_mm} px residui"))
        print(f"  {bid:56} raggio {best_radius}  {best_mm} px residui")
    return results


def build_plates(names=None):
    manifest_by_id = {x["id"]: x for x in json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))}
    if not names:
        names = [x["id"] for x in manifest_by_id.values() if x["testo"] and x["stato"] != "invariato"]
    os.makedirs(PLATES, exist_ok=True)
    done = pictorial = without = 0
    for bid in sorted(names):
        for suff in ("", "_"):
            name = bid + suff
            ims = _load(name)
            if "en" not in ims:
                without += 1; continue
            bb = text_box(ims)
            if not bb:
                pictorial += 1; continue
            plate(ims, bb).save(os.path.join(PLATES, name + ".png"))
            done += 1
        if done and done % 40 == 0:
            print(f"    ...{done} lastre")
    print(f"lastre costruite: {done}")
    print(f"senza testo (immagine lasciata intatta): {pictorial}")
    print(f"senza versione inglese estratta: {without}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "extract":
        extract()
    elif a[0] == "build":
        build_plates(a[1:] or None)
    elif a[0] == "survey":
        survey()
    elif a[0] == "redo":
        redo(a[1:])
    else:
        print(__doc__)
