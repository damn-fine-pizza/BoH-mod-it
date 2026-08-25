"""Rimette in casa il materiale d'arte che il repository non pubblica.

Le copertine dei libri sono arte di Weather Factory. Il repository tiene solo
cio' che e' nostro - le lastre ripulite, il manifest, le sigle, e le copertine
finite dentro il mod, che il kit ufficiale autorizza esplicitamente - e lascia
fuori i due set di partenza. Non e' una perdita: tutt'e due si rifanno da una
fonte legittima, ed e' quello che fa questo script.

    art/originals/  lo ZIP che Weather Factory pubblica sul proprio sito per i
                    modder, con il permesso di partire dalle immagini
                    originali. Chiunque puo' scaricarlo; qui lo scarica lo
                    script. Serve da riferimento: covers.py legge le estratte, e
                    ricade qui solo per i file che nel gioco non esistono
                    (uncatbook.*, wc.*).
    art/extracted/   i quattro set di sprite (en, ru, jp, zh-hans) dentro
                    resources.assets del gioco installato. Li tira fuori chi
                    possiede una copia del gioco, e il lavoro lo fa gia'
                    plates.py extract: qui c'e' solo la chiamata, perche' le due
                    fonti si chiedano allo stesso modo.

Nessuna delle due cartelle torna dentro git: .gitignore le tiene fuori.

Uso:
    python3 tools/sources.py             che cosa c'e' e che cosa manca
    python3 tools/sources.py originals   scarica e scompatta lo ZIP di WF
    python3 tools/sources.py extracted    estrae gli sprite dal gioco installato
    python3 tools/sources.py all       tutt'e due
"""
import os, shutil, sys, tempfile, urllib.request, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

ZIP = "https://weatherfactory.biz/wp-content/uploads/2025/04/book_covers.zip"
ART = os.path.join(PROJ, "art")
ORIGINALS = os.path.join(ART, "originals")
EXTRACTED = os.path.join(ART, "extracted")
CULTURES = ("en", "ru", "jp", "zh-hans")


def count_of(d):
    return len([f for f in os.listdir(d) if f.endswith(".png")]) if os.path.isdir(d) else 0


def originals():
    """Scarica lo ZIP di Weather Factory e ne scompatta i PNG in art/originals/."""
    os.makedirs(ORIGINALS, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    try:
        print(f"scarico {ZIP}")
        # senza User-Agent il sito puo' rispondere 403: ci si presenta col nome
        # del progetto, che e' anche il modo onesto di farsi riconoscere nei log.
        req = urllib.request.Request(ZIP, headers={"User-Agent": "book-of-hours-localization-it"})
        with urllib.request.urlopen(req, timeout=180) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f)
        print(f"  {os.path.getsize(tmp) / 1e6:.1f} MB")
        n = 0
        with zipfile.ZipFile(tmp) as z:
            for entry in z.namelist():
                name = os.path.basename(entry)
                # lo ZIP tiene tutto dentro book_covers/: la cartella si
                # appiattisce, perche' covers.py cerca i file per nome secco.
                if not name.endswith(".png"):
                    continue
                with z.open(entry) as src, open(os.path.join(ORIGINALS, name), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                n += 1
        print(f"scompattati {n} PNG in art/originals/")
    finally:
        os.unlink(tmp)


def extracted():
    """Il gioco installato, via plates.py: la stessa estrazione delle lastre."""
    from plates import extract
    extract()


def state():
    n = count_of(ORIGINALS)
    print(f"art/originals/       {n:>4} PNG   attesi 582"
          f"{'' if n else '   -> python3 tools/sources.py originals'}")
    for c in CULTURES:
        n = count_of(os.path.join(EXTRACTED, c))
        print(f"art/extracted/{c:<8}{n:>4} PNG"
              f"{'' if n else '           -> python3 tools/sources.py extracted'}")
    print(f"art/plates/          {count_of(os.path.join(ART, 'plates')):>4} PNG   "
          f"le nostre, versionate: si rifanno con plates.py build")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        state()
    elif a[0] == "originals":
        originals()
    elif a[0] == "extracted":
        extracted()
    elif a[0] == "all":
        originals()
        extracted()
    else:
        print(__doc__)
