"""L'immagine della scheda del mod: uno scaffale di dorsi con le sigle italiane.

Il gioco la vuole nella radice del mod, PNG, e la sua unica prescrizione e' nel
messaggio d'errore dell'uploader: «The mod needs a 100x100 PNG file named
'cover.png'». Il mod spagnolo pubblicato ne ha una da 300x300, quindi il
quadrato non e' vincolante al pixel; qui se ne fa una da 512, che regge lo zoom
della pagina Workshop e resta ben sotto il megabyte che Steam ammette per
l'anteprima.

Il soggetto non e' un rettangolo con del testo sopra: sono i dorsi veri dei
libri del gioco, gia' riscritti con le sigle italiane - UCdPI per Un Catalogo di
Piaceri Inesplorati, UVB per Una Voce Bianca. E' esattamente cio' che il mod fa
e che si vede aprendo uno scaffale: se le sigle non fossero state rifatte, li'
si leggerebbe ancora aCoUP.

Uso: python3 tools/cover.py [--spines 14]
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, MOD
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SPINES = os.path.join(MOD, "images", "books", "loc_it")
FONT = os.path.join(PROJ, "art", "font", "EBGaramond-Medium.ttf")
OUT_PATH = os.path.join(MOD, "cover.png")
SIDE = 512
BACKGROUND = (18, 15, 13)

# Scelti perche' insieme danno colori diversi e sigle leggibili anche piccole:
# la miniatura nella lista dei mod e' 100x100.
CHOICE = [
    "t.acatalogueofunchartedpleasures_", "t.thelibraryofdust_", "t.anechoofsilence_",
    "t.avoiceinwhite_", "t.thesunsdesign_", "t.ambrosial!_", "t.blacknephrite_",
    "t.againstvitruvius_", "t.adviceoncontainment_", "t.thethreeandthethree_",
    "t.acrownofthorns_", "t.aseventhvoice_",
]


def spines(count_of):
    """I dorsi scelti, piu' altri presi a caso se qualcuno degli scelti manca."""
    present = {f[:-4] for f in os.listdir(SPINES) if f.endswith("_.png")}
    row = [d for d in CHOICE if d in present]
    rest = sorted(present - set(row))
    random.Random(7).shuffle(rest)          # seme fisso: la copertina non cambia a ogni giro
    row += rest[: max(0, count_of - len(row))]
    return [Image.open(os.path.join(SPINES, d + ".png")).convert("RGB") for d in row[:count_of]]


def bookshelf(ims, width, height):
    """I dorsi in fila, appoggiati sul ripiano, scalati alla stessa altezza."""
    ims = [im.resize((max(1, round(im.width * height / im.height)), height), Image.LANCZOS)
           for im in ims]
    tot = sum(im.width for im in ims)
    if tot > width:                       # stringe tutto in proporzione
        k = width / tot
        ims = [im.resize((max(1, round(im.width * k)), round(height * k)), Image.LANCZOS)
               for im in ims]
        tot = sum(im.width for im in ims)
    shelf = Image.new("RGB", (width, max(im.height for im in ims)), BACKGROUND)
    x = (width - tot) // 2
    for im in ims:
        shelf.paste(im, (x, shelf.height - im.height))
        x += im.width
    return shelf


def main():
    count_of = 12
    if "--spines" in sys.argv:
        count_of = int(sys.argv[sys.argv.index("--spines") + 1])
    all_of = spines(count_of * 2)
    canvas = Image.new("RGB", (SIDE, SIDE), BACKGROUND)

    # due ripiani: quello dietro piu' piccolo e piu' scuro, per dare profondita'
    behind = bookshelf(all_of[count_of:], SIDE + 30, 132)
    behind = Image.eval(behind, lambda v: int(v * 0.5))
    canvas.paste(behind, (-15, 62))
    front = bookshelf(all_of[:count_of], SIDE + 30, 172)
    canvas.paste(front, (-15, SIDE - front.height - 22))

    # vignettatura: il gioco e' una casa buia, e la sigla al centro deve staccare
    shadow = Image.new("L", (SIDE, SIDE), 0)
    ImageDraw.Draw(shadow).ellipse((-SIDE // 2, -SIDE // 2, SIDE + SIDE // 2, SIDE + SIDE // 2),
                                  fill=215)
    shadow = shadow.filter(ImageFilter.GaussianBlur(70))
    canvas = Image.composite(canvas, Image.new("RGB", canvas.size, BACKGROUND), shadow)

    # la fascia col nome della lingua, in EB Garamond come le sigle sui dorsi
    d = ImageDraw.Draw(canvas, "RGBA")
    d.rectangle((0, 198, SIDE, 318), fill=(18, 15, 13, 214))
    d.line((44, 199, SIDE - 44, 199), fill=(126, 110, 86, 150))
    d.line((44, 317, SIDE - 44, 317), fill=(126, 110, 86, 150))
    small = ImageFont.truetype(FONT, 24)
    above, sp2 = "BOOK OF HOURS", 5
    width_b = sum(d.textlength(c, font=small) + sp2 for c in above) - sp2
    x = (SIDE - width_b) / 2
    for c in above:
        d.text((x, 213), c, font=small, fill=(154, 140, 116))
        x += d.textlength(c, font=small) + sp2
    font = ImageFont.truetype(FONT, 70)
    text, spacing = "ITALIANO", 9
    width_a = sum(d.textlength(c, font=font) + spacing for c in text) - spacing
    x = (SIDE - width_a) / 2
    for c in text:
        d.text((x, 240), c, font=font, fill=(234, 224, 203))
        x += d.textlength(c, font=font) + spacing

    canvas.save(OUT_PATH, optimize=True)
    print(f"{os.path.relpath(OUT_PATH, PROJ)}: {canvas.size[0]}x{canvas.size[1]}, "
          f"{os.path.getsize(OUT_PATH) / 1024:.0f} KB, {count_of} dorsi in primo piano")



if __name__ == "__main__":
    main()
