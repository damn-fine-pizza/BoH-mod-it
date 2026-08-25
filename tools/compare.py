"""Pagina HTML che affianca ogni copertina originale alla lastra ripulita.

Serve a controllare 486 immagini a colpo d'occhio: a tavolino non si vede
niente, e i difetti di cancellatura si notano solo confrontando.

Uso: python compare.py            -> art/confronto.html
     python compare.py --dirty  -> solo quelle con macchie residue
"""
import base64, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

ART = os.path.join(PROJ, "art")
PLATES = os.path.join(ART, "plates")
ORIG = os.path.join(ART, "estratte", "en")

STYLE = """
:root { color-scheme: dark; }
body { background:#17161a; color:#e8e2d6; font:14px/1.5 system-ui,sans-serif; margin:0; padding:24px; }
h1 { font-size:20px; font-weight:600; margin:0 0 4px; }
p.sotto { color:#9b948a; margin:0 0 24px; }
table { border-collapse:collapse; width:100%; }
td { padding:0; vertical-align:top; }
/* niente max-width qui: in una tabella collassa l'intera colonna a zero, e
   le immagini con max-width:100% diventano larghe zero -- ci sono ma non si
   vedono. I nomi lunghi vanno a capo, che e' meno elegante e funziona. */
tr.nomi td { font:11px ui-monospace,monospace; color:#c4aa7c; padding:10px 8px 4px;
             border-top:1px solid #2c2a30; word-break:break-all; }
tr.img td { padding:0 8px 18px; text-align:center; background:#17161a; }
tr.img img { image-rendering:pixelated; width:286px; height:auto;
             background:#0e0d10; outline:1px solid #2c2a30; }
td.sx { width:50%; } td.dx { width:50%; }
.zoom img { transform:scale(2); transform-origin:center top; margin-bottom:110px; }
"""


def merge_into(path_for):
    with open(path_for, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def page(entries, dest, title, note):
    lines = []
    for name in entries:
        # Le immagini vanno dentro la pagina come data: URI. Coi percorsi,
        # relativi o assoluti che siano, la resa dipende da dove si apre il
        # file e da come il browser tratta le risorse locali; incorporate,
        # non dipende da niente.
        o = merge_into(os.path.join(ORIG, name + ".png"))
        l = merge_into(os.path.join(PLATES, name + ".png"))
        lines.append(
            f'<tr class="nomi"><td class="sx">{name}.png &nbsp;·&nbsp; originale</td>'
            f'<td class="dx">{name}.png &nbsp;·&nbsp; ripulita</td></tr>'
            f'<tr class="img"><td class="sx"><img src="{o}" alt=""></td>'
            f'<td class="dx"><img src="{l}" alt=""></td></tr>')
    html = (f'<!doctype html><meta charset="utf-8"><title>{title}</title>'
            f"<style>{STYLE}</style><h1>{title}</h1>"
            f'<p class="sotto">{note}</p><table>' + "".join(lines) + "</table>")
    open(dest, "w", encoding="utf-8").write(html)
    return len(entries)


def main(only_dirty=False):
    manifest_by_id = json.load(open(os.path.join(ART, "manifest.json"), encoding="utf-8"))
    names = []
    for x in manifest_by_id:
        if x["testo"] and x["stato"] != "invariato":
            for n in (x["id"], x["id"] + "_"):
                if os.path.exists(os.path.join(PLATES, n + ".png")) and \
                   os.path.exists(os.path.join(ORIG, n + ".png")):
                    names.append(n)
    note = "A sinistra l'originale inglese, a destra la lastra con la scritta cancellata."
    if only_dirty:
        from plates import stains
        names = [n for n in names if stains(n)]
        note += " Solo le lastre con inchiostro residuo."
    names = sorted(names)
    if only_dirty:
        dest = os.path.join(ART, "confronto-sporche.html")
        print(f"{dest}: {page(names, dest, 'Copertine con inchiostro residuo', note)} coppie")
        return
    # incorporate, le immagini pesano: una pagina sola sarebbe di decine di
    # megabyte e il browser arrancherebbe. Si spezza, con i collegamenti in cima.
    PER = 60
    blocks = [names[i:i + PER] for i in range(0, len(names), PER)]
    index = " · ".join(
        f'<a href="confronto-{i+1}.html">{i*PER+1}-{min((i+1)*PER, len(names))}</a>'
        for i in range(len(blocks)))
    for i, b in enumerate(blocks):
        dest = os.path.join(ART, f"confronto-{i+1}.html")
        n = page(b, dest, f"Copertine {i*PER+1}-{i*PER+len(b)} di {len(names)}",
                   note + "<br>" + index)
        print(f"{os.path.basename(dest)}: {n} coppie")


if __name__ == "__main__":
    main("--dirty" in sys.argv)
