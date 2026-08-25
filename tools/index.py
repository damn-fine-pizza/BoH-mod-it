"""Pagine di revisione delle copertine: l'indice completo e le sole da controllare.

L'indice serve a vedere tutti i libri insieme -- titolo, sigla, stato -- con la
miniatura accanto, perche' una tabella di soli nomi non dice se una lastra e'
venuta bene. Le miniature sono incorporate in base64: coi percorsi la resa
dipende da dove si apre il file.

Uso: python index.py            -> art/indice.html e art/da-controllare.html
"""
import base64, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ
from plates import stains

ART = os.path.join(PROJ, "art")
PLATES = os.path.join(ART, "plates")
ORIG = os.path.join(ART, "extracted", "en")
MOD = os.path.join(PROJ, "mod", "BookOfHours_italian", "images", "books", "loc_it")

STYLE = """body{background:#17161a;color:#e8e2d6;font:14px/1.5 system-ui,sans-serif;margin:0;padding:24px}
h1{font-size:21px;margin:0 0 4px}h2{font-size:15px;color:#c4aa7c;margin:26px 0 8px;font-weight:600}
p.s{color:#9b948a;margin:0 0 18px;max-width:78ch}
a{color:#9fc4e8}nav a{display:inline-block;margin:0 14px 6px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;color:#c4aa7c;font-weight:600;font-size:11px;text-transform:uppercase;
letter-spacing:.04em;padding:6px 8px;border-bottom:1px solid #3a373f;position:sticky;top:0;background:#17161a}
td{padding:6px 8px;border-bottom:1px solid #232128;vertical-align:middle}
td.sg{font:14px ui-monospace,monospace;color:#f0d9a0;white-space:nowrap}
td.id{font:10px ui-monospace,monospace;color:#7d7688}
img{image-rendering:pixelated;vertical-align:middle;background:#0e0d10;outline:1px solid #2c2a30}
.ok{color:#9fd07a}.ko{color:#e0a0a0}.mano{color:#8fb4d8}
tr:hover td{background:#1e1c22}"""


def mini(path_for, width, colors=64):
    """Miniatura incorporata. Ridotta prima di codificare, o la pagina esplode."""
    if not os.path.exists(path_for):
        return ""
    from PIL import Image
    im = Image.open(path_for).convert("RGB")
    r = width / im.width
    im = im.resize((width, max(1, int(im.height * r))), Image.LANCZOS)
    # Le copertine sono a tinte piatte: una palette indicizzata le comprime di
    # quattro o cinque volte senza differenza visibile, e una pagina da dieci
    # megabyte torna sotto i tre.
    im = im.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def plate_state(books):
    st = {}
    for x in books:
        for n in (x["id"], x["id"] + "_"):
            if os.path.exists(os.path.join(PLATES, n + ".png")):
                st[n] = sum(m[0] for m in stains(n))
    return st


def main():
    manifest_by_id = json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))
    books = sorted([x for x in manifest_by_id if x["testo"] and x["stato"] != "invariato"],
                 key=lambda v: v["en"].lower())
    st = plate_state(books)
    dirty = {n for n, v in st.items() if v}

    def line(x, w, with_mod):
        cells = []
        for n in (x["id"], x["id"] + "_"):
            o, l = mini(os.path.join(ORIG, n + ".png"), w), mini(os.path.join(PLATES, n + ".png"), w)
            cells.append(f'<img src="{o}">' if o else "&mdash;")
            cells.append(f'<img src="{l}">' if l else "&mdash;")
            if with_mod:
                d = mini(os.path.join(MOD, n + ".png"), w)
                cells.append(f'<img src="{d}">' if d else "&mdash;")
        v = st.get(x["id"]), st.get(x["id"] + "_")
        def s(k):
            if k is None:
                return "&mdash;"
            return f'<span class="ok">ok</span>' if k == 0 else f'<span class="ko">{k}&nbsp;px</span>'
        return (f'<tr><td>{x["en"]}</td><td>{x["it"]}</td><td class="sg">{x["sigla"]}</td>'
                + "".join(f"<td>{c}</td>" for c in cells)
                + f'<td>{s(v[0])}</td><td>{s(v[1])}</td><td class="id">{x["id"]}</td></tr>')

    # indice completo, miniature piccole
    header = ('<tr><th>inglese</th><th>italiano</th><th>sigla</th>'
              '<th colspan="2">copertina</th><th colspan="2">dorso</th>'
              '<th>cop.</th><th>dorso</th><th>id</th></tr>')
    lines = "".join(line(x, 44, False) for x in books)
    open(os.path.join(ART, "indice.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Copertine: indice</title>'
        f'<style>{STYLE}</style><h1>Copertine dei libri &mdash; indice</h1>'
        f'<p class="s">{len(books)} libri, {len(st)} lastre, {len(dirty)} con inchiostro residuo. '
        'Per copertina e dorso: a sinistra l\'originale inglese, a destra la lastra ripulita. '
        'Le sigle sono di 1-4 caratteri, come chiede il kit di Weather Factory.</p>'
        f'<nav><a href="da-controllare.html">solo quelle da controllare ({len(dirty)})</a></nav>'
        f'<table>{header}{lines}</table>')

    # solo le sporche, miniature grandi e la versione con la sigla
    to_check = [x for x in books if x["id"] in dirty or x["id"] + "_" in dirty]
    to_check.sort(key=lambda x: -(st.get(x["id"], 0) + st.get(x["id"] + "_", 0)))
    header2 = ('<tr><th>libro</th><th>italiano</th><th>sigla</th>'
               '<th colspan="3">copertina: originale &middot; lastra &middot; con sigla</th>'
               '<th colspan="3">dorso</th><th>cop.</th><th>dorso</th></tr>')
    lines2 = "".join(line(x, 108, True).replace("<td class=\"id\">" + x["id"] + "</td>", "")
                     for x in to_check)
    open(os.path.join(ART, "da-controllare.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Da controllare</title>'
        f'<style>{STYLE}</style><h1>Le {len(to_check)} copertine da controllare</h1>'
        f'<p class="s">Solo i libri in cui almeno una lastra ha inchiostro residuo, dal peggiore in giu\'. '
        'Per copertina e dorso, nell\'ordine: originale inglese, lastra ripulita, e la versione con la '
        'sigla italiana gia\' scritta. Le lastre sono versionate: le versioni '
        'precedenti stanno in <code>git log -- art/plates/</code>.</p>'
        f'<nav><a href="indice.html">torna all\'indice completo ({len(books)})</a></nav>'
        f'<table>{header2}{lines2}</table>')
    print(f"  art/indice.html: {len(books)} libri")
    print(f"  art/da-controllare.html: {len(to_check)} libri, {len(dirty)} lastre sporche")


def compare_en_it(per_page=80):
    """Pagine inglese/italiano per il controllo dei titoli.

    Serve a verificare che la sigla corrisponda al titolo: sotto il nome del
    file ci sono il titolo inglese e quello italiano, e accanto le due
    copertine. Cosi' l'errore -- una sigla che non deriva dal titolo, un titolo
    tradotto male -- si vede senza incrociare due documenti.
    """
    manifest_by_id = json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))
    books = sorted([x for x in manifest_by_id if x["testo"] and x["stato"] != "invariato"],
                 key=lambda v: v["en"].lower())
    blocks = [books[i:i + per_page] for i in range(0, len(books), per_page)]
    names = [f"en-it-{i+1}.html" for i in range(len(blocks))]
    for i, block in enumerate(blocks):
        lines = []
        for x in block:
            cells = []
            for suff in ("", "_"):
                n = x["id"] + suff
                for folder in (ORIG, MOD):
                    m = mini(os.path.join(folder, n + ".png"), 124)
                    cells.append(f'<img src="{m}">' if m else "&mdash;")
            lines.append(
                f'<tr><td><div class="fn">{x["id"]}.png</div>'
                f'<div class="en">{x["en"]}</div>'
                f'<div class="it">{x["it"]}</div>'
                f'<div class="sg">{x["sigla"]}</div></td>'
                + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        nav = " · ".join(f'<a href="{m}">{j*per_page+1}-{min((j+1)*per_page, len(books))}</a>'
                         if j != i else f"<b>{j*per_page+1}-{min((j+1)*per_page, len(books))}</b>"
                         for j, m in enumerate(names))
        open(os.path.join(ART, names[i]), "w", encoding="utf-8").write(
            '<!doctype html><meta charset="utf-8"><title>Inglese e italiano</title>'
            f'<style>{STYLE}{EXTRA}</style><h1>Copertine: inglese e italiano</h1>'
            '<p class="s">Sotto il nome del file, il titolo inglese e quello italiano, '
            'e la sigla che ne deriva. Per copertina e dorso: originale a sinistra, '
            'nostra a destra.</p>'
            f'<nav>{nav}</nav><table>'
            '<tr><th>libro</th><th>cop. EN</th><th>cop. IT</th><th>dorso EN</th><th>dorso IT</th></tr>'
            + "".join(lines) + '</table>')
    print(f"  {len(blocks)} pagine en-it, {len(books)} libri")


EXTRA = """.fn{font:11px ui-monospace,monospace;color:#7d7688}
.en{font-size:14px;color:#e8e2d6;margin-top:2px}
.it{font-size:14px;color:#b8d8b0;margin-top:1px}
.sg{font:16px ui-monospace,monospace;color:#f0d9a0;margin-top:4px}
td{max-width:420px}"""


def unique():
    """Una pagina sola con tutte le copertine, e le immagini NON incorporate.

    Le immagini sono incorporate. Coi percorsi -- relativi o assoluti che siano
    -- la pagina non funziona dentro un browser in sandbox, che l'albero del
    progetto non lo vede: Firefox Flatpak mostra la tabella e nessuna immagine.
    Incorporate, il file si apre da qualunque posto.

    Per non arrivare a venti megabyte le miniature sono ridotte e indicizzate:
    queste copertine sono a tinte piatte e una palette a 32 colori le comprime
    moltissimo senza differenza visibile.
    """
    manifest_by_id = json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))
    books = sorted([x for x in manifest_by_id if x["testo"] and x["stato"] != "invariato"],
                 key=lambda v: v["en"].lower())
    lines = []
    for x in books:
        cells = []
        for suff in ("", "_"):
            n = x["id"] + suff
            for folder in (ORIG, MOD):
                m = mini(os.path.join(folder, n + ".png"), 104, colors=32)
                cells.append(f'<img src="{m}" loading="lazy">' if m else "&mdash;")
        lines.append(f'<tr><td><div class="fn">{x["id"]}.png</div>'
                     f'<div class="en">{x["en"]}</div><div class="it">{x["it"]}</div>'
                     f'<div class="sg">{x["sigla"]}</div></td>'
                     + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    open(os.path.join(ART, "tutte.html"), "w", encoding="utf-8").write(
        '<!doctype html><meta charset="utf-8"><title>Tutte le copertine</title>'
        f'<style>{STYLE}{EXTRA}img{{width:104px}}</style>'
        f'<h1>Tutte le copertine &mdash; {len(books)} libri</h1>'
        '<p class="s">Immagini non incorporate: la pagina pesa poche decine di kilobyte '
        "ma va aperta dentro <code>art/</code>, perche' i percorsi sono relativi. "
        'Per copertina e dorso: originale inglese a sinistra, nostra a destra.</p>'
        '<table><tr><th>libro</th><th>cop. EN</th><th>cop. IT</th>'
        '<th>dorso EN</th><th>dorso IT</th></tr>' + "".join(lines) + '</table>')
    print(f"  art/tutte.html: {len(books)} libri")


if __name__ == "__main__":
    if "--single" in sys.argv:
        unique()
    elif "--en-it" in sys.argv:
        compare_en_it()
    else:
        main()
