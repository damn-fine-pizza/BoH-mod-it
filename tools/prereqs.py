"""Che cosa serve per rigenerare, e una prova che dice se c'e' davvero.

Il repository tiene solo cio' che e' nostro: il dizionario, le lastre ripulite,
il manifest, il font dei libri. Il resto - le dipendenze Python, il gioco
installato, l'arte di Weather Factory, un font di sistema per le insegne - si
mette insieme prima. Se manca un pezzo la rigenerazione non si rifiuta di
partire: arriva a meta' e muore con un errore che non dice quale sia il pezzo.
Questo script lo dice prima, e con --verify lo dimostra rigenerando per davvero.

Uso:
    python3 tools/prereqs.py           la lista, con quello che manca
    python3 tools/prereqs.py --verify   rigenera in una cartella temporanea e
                                         confronta con quello che spediamo

Esce con 1 se manca qualcosa di essenziale, cosi' si puo' mettere in testa a un
altro script senza doverne leggere l'uscita.
"""
import contextlib, importlib.util, io, os, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIP = "pip install -r requirements.txt"


def version(package):
    import importlib.metadata as meta
    try:
        return meta.version(package)
    except Exception:
        return None


def module_name(name):
    return importlib.util.find_spec(name) is not None


def _bohloc():
    """Importabile solo se c'e' json5: senza, i percorsi non si possono chiedere."""
    try:
        import bohloc
        return bohloc
    except Exception:
        return None


def collect():
    """-> [(gruppo, essenziale, nome, dettaglio, rimedio)], dettaglio None = manca"""
    b = _bohloc()
    v = sys.version_info
    r = [("per il testo", True, "Python >= 3.9",
          f"{v.major}.{v.minor}.{v.micro}" if v >= (3, 9) else None,
          "una versione piu' recente di Python")]

    for group, essential, package, mod in [
            ("per il testo", True, "json5", "json5"),
            ("per le copertine", True, "Pillow", "PIL"),
            ("per le copertine", True, "numpy", "numpy"),
            ("per le copertine", False, "UnityPy", "UnityPy")]:
        r.append((group, essential, package, version(package) if module_name(mod) else None, PIP))

    it = os.path.join(PROJ, "translations", "it.json")
    n = None
    if os.path.exists(it):
        import json
        # il dizionario vero sta sotto 'strings': 'overrides' sono le eccezioni
        d = json.load(open(it, encoding="utf-8"))
        n = f"{len(d.get('strings', d)):,} voci".replace(",", ".")
    r.append(("per il testo", True, "translations/it.json", n, "e' nel repository: git status"))

    font = os.path.join(PROJ, "art", "font")
    cuts = [f for f in os.listdir(font) if f.endswith(".ttf")] if os.path.isdir(font) else []
    r.append(("per le copertine", True, "art/font/ (EB Garamond)",
              f"{len(cuts)} tagli" if len(cuts) >= 4 else None, "e' nel repository: git status"))

    plates = os.path.join(PROJ, "art", "plates")
    how_many = len([f for f in os.listdir(plates) if f.endswith(".png")]) if os.path.isdir(plates) else 0
    r.append(("per le copertine", True, "art/plates/",
              f"{how_many} PNG" if how_many else None, "e' nel repository: git status"))

    extracted_dir = os.path.join(PROJ, "art", "extracted", "en")
    how_many = len(os.listdir(extracted_dir)) if os.path.isdir(extracted_dir) else 0
    r.append(("per le copertine", True, "art/extracted/en/",
              f"{how_many} PNG" if how_many else None, "python3 tools/sources.py extracted"))

    orig = os.path.join(PROJ, "art", "originals")
    how_many = len(os.listdir(orig)) if os.path.isdir(orig) else 0
    r.append(("per le copertine", False, "art/originals/",
              f"{how_many} PNG" if how_many else None, "python3 tools/sources.py originals"))

    if b:
        r.append(("per le copertine", False, "il gioco installato",
                  "c'e'" if os.path.isdir(b.CORE) else None,
                  "serve per estrarre gli sprite: percorsi.json, chiave «game»"))
        r.append(("per le insegne", False, "font lineare di sistema",
                  os.path.basename(b.path_for("font_insegna", "/usr/share/fonts/urw-base35/NimbusSans-Bold.otf"))
                  if os.path.exists(b.path_for("font_insegna", "/usr/share/fonts/urw-base35/NimbusSans-Bold.otf")) else None,
                  "dnf install urw-base35-fonts | apt install fonts-urw-base35"))
        r.append(("per le insegne", False, "il kit delle immagini",
                  "c'e'" if os.path.isdir(b.KIT) else None,
                  "lo manda Weather Factory a chi lo chiede: percorsi.json, chiave «kit»"))
        r.append(("facoltativi", False, "cartella mods del gioco",
                  "c'e'" if os.path.isdir(b.MODS) else None,
                  "serve solo a pack.py --install: percorsi.json, chiave «mods»"))
        r.append(("facoltativi", False, "mod spagnolo (metro di confronto)",
                  "c'e'" if os.path.isdir(b.ES) else None,
                  "Steam Workshop 1028310/3784793429, poi percorsi.json, chiave «loc_es»"))
    else:
        r.append(("per le copertine", True, "i percorsi del gioco", None,
                  f"prima {PIP}: senza json5 non si legge percorsi.json"))
    return r


def show_list():
    lines = collect()
    missing_count = optional = 0
    for group in ("per il testo", "per le copertine", "per le insegne", "facoltativi"):
        in_group = [x for x in lines if x[0] == group]
        if not in_group:
            continue
        print(f"\n{group}")
        for _, essential, name, detail, remedy in in_group:
            if detail:
                print(f"  ok    {name:<34}{detail}")
            else:
                print(f"  MANCA {name:<34}-> {remedy}")
                missing_count += essential
                optional += not essential
    print()
    # un facoltativo che manca non ferma niente, ma dire «c'e' tutto» con una
    # riga MANCA sotto gli occhi e' il modo migliore per non farsi credere.
    if missing_count:
        print(f"manca {missing_count} requisito essenziale: la rigenerazione si fermerebbe a meta'."
              if missing_count == 1 else
              f"mancano {missing_count} requisiti essenziali: la rigenerazione si fermerebbe a meta'.")
    elif optional:
        print(f"l'essenziale c'e'; {optional} facoltativo manca, e limita solo quello che"
              if optional == 1 else
              f"l'essenziale c'e'; {optional} facoltativi mancano, e limitano solo quello che")
        print("gli sta accanto qui sopra. python3 tools/prereqs.py --verify per il resto.")
    else:
        print("c'e' tutto. python3 tools/prereqs.py --verify per vederlo all'opera.")
    return 1 if missing_count else 0


def verify():
    """Rigenera davvero, in una cartella temporanea, e confronta con lo spedito."""
    results = []
    print("\nprova di rigenerazione (niente viene scritto nel repository)")

    try:
        import apply
        silent = io.StringIO()
        with contextlib.redirect_stdout(silent):
            apply.main(dry=True)
        tail = [r for r in silent.getvalue().splitlines() if r.strip()][-1]
        results.append((True, f"apply.py --dry: {tail.strip()}"))
    except Exception as e:
        results.append((False, f"apply.py --dry non arriva in fondo: {e}"))

    tmp = tempfile.mkdtemp(prefix="boh-requisiti-")
    try:
        import covers
        shipped = os.path.join(covers.DEST_MOD, "t.blacknephrite.png")
        real_dest = covers.DEST_MOD
        covers.DEST_MOD = tmp
        result = covers.one_cover("t.blacknephrite", covers.manifest())
        covers.DEST_MOD = real_dest
        fresh = os.path.join(tmp, "t.blacknephrite.png")
        if not os.path.exists(fresh):
            results.append((False, f"la copertina non e' stata scritta: {result}"))
        elif not os.path.exists(shipped):
            results.append((True, "copertina rigenerata (non c'e' quella spedita da confrontare)"))
        else:
            equal = open(fresh, "rb").read() == open(shipped, "rb").read()
            results.append((equal, "la copertina rigenerata e' identica a quella spedita"
                          if equal else "la copertina rigenerata NON coincide con quella spedita"))
    except Exception as e:
        results.append((False, f"covers.py non rigenera: {e}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    b = _bohloc()
    if b:
        try:
            f = os.path.join(b.CORE, "cultures", "en", "culture.json")
            results.append((os.path.exists(f) and bool(b.read(f)), "i file del gioco si leggono"))
        except Exception as e:
            results.append((False, f"i file del gioco non si leggono: {e}"))
        try:
            from PIL import ImageFont
            p = b.path_for("font_insegna", "/usr/share/fonts/urw-base35/NimbusSans-Bold.otf")
            ImageFont.truetype(p, 20)
            results.append((True, f"il font delle insegne si apre ({os.path.basename(p)})"))
        except Exception as e:
            results.append((False, f"il font delle insegne non si apre: {e}"))

    for ok, text in results:
        print(f"  {'ok   ' if ok else 'NO   '}{text}")
    print()
    broken = [t for ok, t in results if not ok]
    print("la catena regge: da qui si rigenera tutto." if not broken
          else f"{len(broken)} prove non passano: vedi sopra.")
    return 1 if broken else 0


if __name__ == "__main__":
    exit_code = show_list()
    if "--verify" in sys.argv:
        exit_code = verify() or exit_code
    sys.exit(exit_code)
