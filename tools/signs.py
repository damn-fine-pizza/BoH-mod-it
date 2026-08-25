"""Rifà in italiano le immagini del gioco che portano il testo disegnato dentro.

Sono le scritte che nessuna traduzione del JSON può toccare: le etichette sui
luoghi della mappa (CUCURBIT BRIDGE, CROWCROSS SANDS), l'insegna dell'ufficio
postale, i cartelli. Weather Factory le distribuisce apposta - «Sorry, you will
need to provide your own images» - e il kit ne fornisce 45, contando le varianti
illuminate.

Il metodo è quello delle copertine dei libri: si misura l'originale e si
ricompone, invece di ridisegnare a occhio. Di ogni etichetta si ricavano dal
file stesso il colore, il numero di righe, l'altezza delle maiuscole, quella del
maiuscoletto, la larghezza occupata e la curvatura della base; poi il testo
italiano viene composto con le stesse misure, dentro un'immagine delle stesse
dimensioni - che è il vincolo vero, perché il gioco posiziona lo sprite dove
sta, e un file più largo sposterebbe la scritta sulla mappa.

Le varianti `.glowy` sono la stessa scritta con un alone: si rigenerano
sfocando la scritta nuova, con lo stesso raggio misurato sull'originale.

Uso:
    python3 tools/signs.py              rifà tutte quelle previste
    python3 tools/signs.py --list      dice che cosa farebbe, senza scrivere
    python3 tools/signs.py label.cucurbit.bridge   una sola
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, MOD, KIT, path_for
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

DEST = os.path.join(MOD, "images", "localised", "loc_it")
FONT = os.path.join(PROJ, "art", "font", "EBGaramond-Regular.ttf")
SPACING = 0.28          # quanto si allarga lo spazio fra parole, in frazioni di corpo
# L'insegna dell'ufficio postale non e' in Garamond ma in un lineare: e' una
# targa smaltata, non una scritta sulla mappa.
SIGN_FONT = path_for("font_insegna",
                        "/usr/share/fonts/urw-base35/NimbusSans-Bold.otf",
                        "/usr/share/fonts/gnu-free/FreeSansBold.otf",
                        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf")

# Le insegne del villaggio: targa (riquadro), testo inglese, testo italiano.
# Solo l'ufficio postale ha del testo traducibile; le altre portano nomi propri
# - THE SWEET BONES, OLD RECTORY, COFFINS & CRADLES - che restano.
SIGNS = {
    "village.postoffice": ((316, 379, 441, 423), "POST OFFICE", "UFFICIO POSTALE"),
    "village.postoffice.closed": ((316, 379, 441, 423), "POST OFFICE", "UFFICIO POSTALE"),
}

# Le rese vengono dal corpus, non inventate qui: «St Brandan's Cove» è già
# «Baia di St Brandan» nel dizionario, «Brancrug village» è «Villaggio di
# Brancrug», «The Atlantic Ocean» è «L'Oceano Atlantico». Hush House resta
# invariata per il punto 2-bis delle convenzioni, e non compare in questa lista.
#
# Accanto alla resa italiana c'è il testo inglese riga per riga: serve a
# calibrare. Rendendo l'inglese con EB Garamond e confrontando il risultato con
# l'immagine originale si ricavano il corpo e la spaziatura veri, e con quelli
# si compone l'italiano - invece di spaziare le lettere fino a riempire la
# larghezza, che sparpagliava «SABBIE DI» per farlo largo quanto «CROWCROSS».
LABELS = {
    "label.cucurbit.bridge": (["CUCURBIT BRIDGE"], ["PONTE DEL CUCURBIT"]),
    "label.crowcross.sands": (["CROWCROSS", "SANDS"], ["SABBIE DI", "CROWCROSS"]),
    "label.atlantic.ocean": (["ATLANTIC", "OCEAN"], ["OCEANO", "ATLANTICO"]),
    "label.brandans.cove": (["ST. BRANDAN’S", "COVE"], ["BAIA DI", "ST. BRANDAN"]),
    "label.brancrug.village": (["BRANCRUG VILLAGE"], ["VILLAGGIO DI BRANCRUG"]),
}


def lines_of(alpha, threshold=16):
    """Le bande orizzontali che contengono testo."""
    present = (alpha > threshold).any(axis=1)
    lines, inside = [], None
    for y, c in enumerate(present):
        if c and inside is None:
            inside = y
        elif not c and inside is not None:
            if y - inside > 8:
                lines.append((inside, y))
            inside = None
    if inside is not None:
        lines.append((inside, len(present)))
    return lines


def measure(path_for):
    """Colore, righe, altezze e curvatura della scritta originale."""
    im = Image.open(path_for).convert("RGBA")
    a = np.asarray(im)
    alpha = a[..., 3]
    full_items = a[alpha > 200][:, :3]
    color = tuple(int(v) for v in full_items.mean(axis=0)) if len(full_items) else (247, 226, 185)
    out = []
    for y0, y1 in lines_of(alpha):
        band = alpha[y0:y1]
        col = (band > 16).any(axis=0)
        xs = np.nonzero(col)[0]
        if len(xs) == 0:
            continue
        # la base della riga, colonna per colonna: dice se la scritta è arcuata
        bases = []
        for x in range(xs.min(), xs.max() + 1, max(1, (xs.max() - xs.min()) // 40)):
            ys = np.nonzero(band[:, x] > 16)[0]
            if len(ys):
                bases.append((x, y0 + ys.max()))
        curve = np.polyfit([b[0] for b in bases], [b[1] for b in bases], 2) if len(bases) > 6 else None
        out.append({"y0": y0, "y1": y1, "x0": int(xs.min()), "x1": int(xs.max()),
                    "altezza": y1 - y0, "curva": curve})
    return im, color, out


def fonts(size, font_path):
    """Il maiuscoletto del gioco: iniziale piena, il resto a poco più di tre
    quarti."""
    return (ImageFont.truetype(font_path, max(6, int(size))),
            ImageFont.truetype(font_path, max(5, int(size * 0.76))))


def width_of(d, text, size, tracking, font_path):
    large, small = fonts(size, font_path)
    tot = 0
    for i, c in enumerate(text):
        f = large if (i == 0 or text[i - 1] == " ") else small
        tot += d.textlength(c, font=f)
        if c == " ":
            tot += size * SPACING          # fra parole ci vuole aria, come nell'originale
    return tot + tracking * max(0, len(text) - 1)


def calibrate(d, text_en, m, font_path):
    """Corpo e spaziatura che riproducono l'originale.

    Il corpo si ricava dall'altezza delle maiuscole (in EB Garamond la cap
    height è circa due terzi del corpo); la spaziatura è quel che resta della
    larghezza misurata, diviso gli spazi fra le lettere."""
    size = m["altezza"] / 0.70
    for _ in range(24):                       # aggiusta il corpo sull'altezza vera
        large, _p = fonts(size, font_path)
        top = large.getbbox("H")[3] - large.getbbox("H")[1]
        if abs(top - m["altezza"]) <= 1:
            break
        size *= m["altezza"] / max(1, top)
    full = width_of(d, text_en, size, 0, font_path)
    tracking = ((m["x1"] - m["x0"]) - full) / max(1, len(text_en) - 1)
    # Mai negativo: il font che usiamo non e' identico a quello dell'originale, e
    # una spaziatura negativa faceva accavallare le lettere di VILLAGGIO DI
    # BRANCRUG. Se non ci sta, si stringe il corpo, non le lettere.
    return size, max(0.0, tracking)


def write_row(canvas, text, text_en, m, color, font_path):
    """Compone una riga con il corpo e la spaziatura dell'originale, centrata
    dove stava la scritta inglese. Se l'italiano è più lungo, si stringe il
    corpo finché entra: mai le lettere sparpagliate."""
    d = ImageDraw.Draw(canvas)
    size, tracking = calibrate(d, text_en, m, font_path)
    max_width = canvas.width - 2 * min(m["x0"], canvas.width - m["x1"])
    while width_of(d, text, size, tracking, font_path) > max_width and size > 8:
        size *= 0.97
        tracking *= 0.97
    width_a = width_of(d, text, size, tracking, font_path)
    large, small = fonts(size, font_path)
    x = (canvas.width - width_a) / 2
    orig_center = (m["x0"] + m["x1"]) / 2
    start = x
    for i, c in enumerate(text):
        f = large if (i == 0 or text[i - 1] == " ") else small
        y = m["y1"]
        if m["curva"] is not None:
            # la curvatura dell'originale, letta al punto corrispondente
            fraction = (x - start) / max(1, width_a)
            xo = m["x0"] + fraction * (m["x1"] - m["x0"])
            y = float(np.polyval(m["curva"], xo))
        d.text((x, y), c, font=f, fill=color, anchor="ls")
        x += d.textlength(c, font=f) + tracking + (size * SPACING if c == " " else 0)
    return canvas


def redo_plaque(name, box, text_en, text_it):
    """Sostituisce il testo su una targa: si riempie la zona col colore della
    targa stessa e si riscrive, con lo stesso lineare e lo stesso bianco."""
    orig = os.path.join(KIT, name + ".png")
    if not os.path.exists(orig):
        print(f"  {name}: manca l'originale nel kit")
        return
    im = Image.open(orig).convert("RGBA")
    x0, y0, x1, y1 = box
    area = np.asarray(im.crop(box).convert("RGB")).reshape(-1, 3)
    light_ones = area[(area > 180).all(axis=1)]
    dark = area[(area < 110).all(axis=1)]
    ink = tuple(int(v) for v in light_ones.mean(axis=0)) if len(light_ones) else (245, 240, 230)
    bottom = tuple(int(v) for v in dark.mean(axis=0)) if len(dark) else (58, 48, 44)

    d = ImageDraw.Draw(im)
    # la targa si ridipinge tutta, cosi' non restano frammenti delle lettere
    d.rectangle((x0 + 2, y0 + 2, x1 - 2, y1 - 2), fill=bottom + (255,))
    width, height = (x1 - x0) * 0.88, (y1 - y0) * 0.46
    size = height
    while True:
        f = ImageFont.truetype(SIGN_FONT, max(6, int(size)))
        bb = d.textbbox((0, 0), text_it, font=f)
        if (bb[2] - bb[0]) <= width or size <= 6:
            break
        size *= 0.96
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text_it, font=f,
           fill=ink + (255,), anchor="mm")
    os.makedirs(DEST, exist_ok=True)
    im.save(os.path.join(DEST, name + ".png"))
    # la variante illuminata usa la stessa targa, ripresa dal file .highlight
    ev = os.path.join(KIT, name + ".highlight.png")
    if os.path.exists(ev):
        im2 = Image.open(ev).convert("RGBA")
        im2.paste(im.crop(box), (x0, y0))
        im2.save(os.path.join(DEST, name + ".highlight.png"))
    print(f"  {name}: targa rifatta ({text_en} -> {text_it}), corpo {int(size)}")


def redo_tablet(name, tablet, text_area, text, text_color=None):
    """Il cartello di legno: si cancella la scritta ricopiando una striscia
    pulita della tavoletta - così restano venature e graffi - e si riscrive.

    Ridipingere un rettangolo pieno, come si fa per la targa smaltata
    dell'ufficio postale, qui si vedrebbe: la tavoletta ha una texture."""
    orig = os.path.join(KIT, name + ".png")
    if not os.path.exists(orig):
        print(f"  {name}: manca l'originale nel kit")
        return
    im = Image.open(orig).convert("RGBA")
    tx0, ty0, tx1, ty1 = tablet
    x0, y0, x1, y1 = text_area
    # Una striscia della tavoletta senza lettere, presa SOTTO la scritta: sopra
    # c'è il bordo scuro, e ripetendolo restavano due righe fantasma in mezzo al
    # cartello.
    alt = max(4, (ty1 - y1) - 4)
    cleaned = im.crop((tx0, y1 + 2, tx1, y1 + 2 + alt))
    y = y0 - 3
    while y < y1 + 3:
        im.paste(cleaned, (tx0, y))
        y += alt
    d = ImageDraw.Draw(im)
    if text_color is None:
        text_color = (121, 92, 69)
    width = (x1 - x0) * 1.06
    size = (y1 - y0) * 1.5
    while True:
        f = ImageFont.truetype(FONT, max(6, int(size)))
        bb = d.textbbox((0, 0), text, font=f)
        if (bb[2] - bb[0]) <= width or size <= 6:
            break
        size *= 0.96
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=f,
           fill=text_color + (255,), anchor="mm")
    os.makedirs(DEST, exist_ok=True)
    im.save(os.path.join(DEST, name + ".png"))
    print(f"  {name}: cartello rifatto (-> {text}), corpo {int(size)}")


def halo(im, radius, force=1.0):
    """La variante illuminata: la scritta stessa, sfocata sotto di sé."""
    blurred = im.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(blurred).astype(np.float32)
    a[..., 3] = np.clip(a[..., 3] * force, 0, 255)
    bottom = Image.fromarray(a.astype("uint8"), "RGBA")
    bottom.alpha_composite(im)
    return bottom


def run_all(name, data, verify=False):
    lines_en, lines = data
    orig = os.path.join(KIT, name + ".png")
    if not os.path.exists(orig):
        print(f"  {name}: manca l'originale nel kit")
        return
    im, color, measures = measure(orig)
    if len(measures) != len(lines):
        print(f"  {name}: l'originale ha {len(measures)} righe, il testo italiano {len(lines)}")
    canvas = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for m, text, text_en in zip(measures, lines, lines_en):
        write_row(canvas, text, text_en, m, color + (255,), FONT)
    if verify:
        print(f"  {name}: {im.size}, {len(measures)} righe, colore {color} -> {' / '.join(lines)}")
        return
    os.makedirs(DEST, exist_ok=True)
    canvas.save(os.path.join(DEST, name + ".png"))
    # la variante illuminata, se il kit ce l'ha
    glowy = os.path.join(KIT, name + ".glowy.png")
    if os.path.exists(glowy):
        g = Image.open(glowy).convert("RGBA")
        radius = max(6, int(min(g.size) * 0.06))
        halo(canvas, radius).save(os.path.join(DEST, name + ".glowy.png"))
    print(f"  {name}: fatta ({' / '.join(lines)})")


def main():
    verify = "--list" in sys.argv
    chosen_ones = [a for a in sys.argv[1:] if not a.startswith("--")]
    for name, data in LABELS.items():
        if chosen_ones and name not in chosen_ones:
            continue
        run_all(name, data, verify)
    if not verify:
        for name, (box, en, it) in SIGNS.items():
            if chosen_ones and name not in chosen_ones:
                continue
            redo_plaque(name, box, en, it)
        if not chosen_ones or "moor sign 3" in chosen_ones:
            # «the Moor» è «la Brughiera» in tutte e dieci le occorrenze del corpus
            redo_tablet("moor sign 3", (54, 87, 236, 167), (70, 110, 217, 143), "BRUGHIERA")
    if not verify:
        print(f"\nin {os.path.relpath(DEST, PROJ)}")



if __name__ == "__main__":
    main()
