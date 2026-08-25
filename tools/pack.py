"""Costruisce il pacchetto da pubblicare: solo cio' che il gioco legge.

L'albero di lavoro `mod/BookOfHours_italian/` pesa 27 MB, ma 13 sono materiale
di riferimento - la copia del mod francese e quella dell'originale inglese, che
servono a chi traduce e non a chi gioca. Copiarlo tutto e' comodo per provare in
locale ed e' sbagliato per pubblicare. Qui si copia da una lista di cose
ammesse, non si esclude da una lista di cose sgradite: se domani nascesse una
cartella nuova, resterebbe fuori finche' qualcuno non decide che ci vuole stare.

L'ordine dei passi non e' arbitrario:

 1. `apply.py`, perche' il pacchetto non possa mai essere piu' vecchio del
    dizionario. E' successo di pubblicare l'albero senza rigenerarlo.
 2. I cancelli. Se uno non e' pulito il pacchetto non si costruisce: un mod
    rotto pubblicato lo scaricano in cento prima che uno se ne accorga.
 3. La copia, il synopsis, lo zip.
 4. Il resoconto: quanto pesa e che cosa e' rimasto fuori. E' il controllo che
    dice a colpo d'occhio se i 13 MB di riferimento sono rientrati.

La versione sta in un posto solo, `translations/mod.json`, e da li' finisce nel
synopsis. Se lo zip di quella versione esiste gia', pack.py si ferma: e' il modo
per non pubblicare due contenuti diversi con lo stesso numero.

`serapeum_catalogue_number.txt` non si crea e non si copia. Contiene l'id
dell'oggetto Workshop e lo scrive il gioco: ModManager.TryWritePublishedFileId
lo salva con File.WriteAllText dopo che Steam ha creato l'oggetto, e
GetPublishedFileIdForMod lo rilegge per decidere se creare o aggiornare.
Scriverlo a mano vuol dire dire al gioco di aggiornare un oggetto altrui.

Uso:
    python3 tools/pack.py                 costruisce dist/ e lo zip
    python3 tools/pack.py --all         aggiunge i cancelli lenti (terms.py)
    python3 tools/pack.py --force         ricostruisce anche se lo zip esiste
    python3 tools/pack.py --no-zip     solo la cartella, per provarla in locale
                                          (non tocca lo zip, quindi non serve --force)
    python3 tools/pack.py --install      e poi la copia nella cartella mods del gioco
"""
import json, os, re, shutil, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, MOD, MODS

TOOLS = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(PROJ, "translations", "mod.json")
DIST = os.path.join(PROJ, "dist")
MOD_NAME = os.path.basename(MOD)

# Cio' che il gioco legge davvero. Le chiavi sono percorsi dentro il mod.
ALLOWED = [
    ("content", "cartella", "la cultura 'it' e le 295 label dell'interfaccia"),
    ("images", "cartella", "le copertine e i dorsi ridisegnati (images/books/loc_it)"),
    ("loc/loc_it", "cartella", "i contenuti tradotti"),
    ("cover.png", "file", "l'immagine della scheda, che l'uploader del gioco pretende"),
]
# Generato da qui, non copiato: vedi synopsis()
GENERATED = ["synopsis.json"]

GATES = [
    ("validate.py", [], "glossario, neutro, markup, glifi"),
    ("prose.py", [], "ortotipografia della prosa"),
    ("integrity.py", [], "tag e a-capo nei file veri"),
    ("glyphcheck.py", [], "glifi contro l'atlante del font"),
    ("checkpart.py", ["--dictionary"], "rese rimaste in inglese"),
    ("identical.py", [], "stringhe ferme sull'inglese: buchi contro scelte"),
    ("grammar.py", [], "accordi, elisioni, articoli"),
    ("accords.py", [], "articoli e preposizioni intorno ai nomi di gioco"),
    ("logic.py", [], "numeri, negazioni e segni contro l'originale"),
]
SLOW = [("terms.py", [], "label contro prosa (minuti)"),
         ("consistency.py", [], "un termine, una resa (minuti)")]


def weight(path_for):
    if os.path.isfile(path_for):
        return os.path.getsize(path_for)
    tot = 0
    for dirpath, _, files in os.walk(path_for):
        tot += sum(os.path.getsize(os.path.join(dirpath, f)) for f in files)
    return tot


def mb(n):
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{n / 1024:.0f} KB"


def run_tool(script, args, explain):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args],
                       capture_output=True, text=True, cwd=PROJ)
    ok = r.returncode == 0
    last = [l for l in r.stdout.strip().split("\n") if l.strip()]
    print(f"  {'ok  ' if ok else 'NO  '}{script:16} {explain}")
    if not ok:
        print("      " + "\n      ".join(last[-12:]))
    return ok


def synopsis(meta):
    """Il synopsis nel formato del kit, dai metadati: name, author, version,
    description, description_long, piu' i tag che lo Workshop mostra."""
    return {k: meta[k] for k in ("name", "author", "version", "description",
                                 "description_long", "tags") if k in meta}


def main():
    meta = json.load(open(META, encoding="utf-8"))
    version = meta["version"]
    # Il gioco si versiona a quattro componenti - version.txt dice 2026.5.g.1 -
    # e il mod segue la stessa forma. La forma si fissa adesso, prima della
    # prima pubblicazione: un numero cambiato dopo lascia in giro pacchetti
    # numerati in due modi, e non si sa piu' quale venga prima.
    if not re.fullmatch(r"\d+\.\d+\.[0-9a-z]+\.\d+", version):
        print(f"versione «{version}»: la forma e' a quattro componenti, come "
              f"quella del gioco (2026.5.g.1).")
        print(f"Si corregge in {os.path.relpath(META, PROJ)}.")
        return 1
    final_zip = os.path.join(DIST, f"{MOD_NAME}-{version}.zip")
    writes_zip = "--no-zip" not in sys.argv
    # il guardiano difende dal pubblicare due contenuti diversi con lo stesso
    # numero: riguarda lo zip, non la cartella. Con --no-zip nessuno zip
    # viene scritto, e fermarsi li' costringeva a --force per costruire una
    # cartella di prova - cioe' a zittire un controllo per fare una cosa che
    # quel controllo non doveva impedire.
    if writes_zip and os.path.exists(final_zip) and "--force" not in sys.argv:
        print(f"esiste gia' {os.path.relpath(final_zip, PROJ)}.")
        print(f"Alza \"version\" in {os.path.relpath(META, PROJ)}, oppure --force.")
        return 1

    print(f"== {meta['name']} {version} ==\n")
    print("1. rigenero i file del mod dal dizionario")
    if not run_tool("apply.py", [], "apply.py"):
        return 1

    print("\n2. cancelli")
    checks = GATES + (SLOW if "--all" in sys.argv else [])
    failed = [s for s, a, d in checks if not run_tool(s, a, d)]
    if failed:
        print(f"\n{len(failed)} cancello/i non pulito/i: non costruisco il pacchetto.")
        return 1
    if "--all" not in sys.argv:
        print("      (terms.py non e' stato lanciato: --all lo include)")

    print("\n3. copio")
    outside = os.path.join(DIST, MOD_NAME)
    if os.path.exists(outside):
        shutil.rmtree(outside)
    os.makedirs(outside)
    included = []
    for rel, kind, explain in ALLOWED:
        source = os.path.join(MOD, rel)
        if not os.path.exists(source):
            print(f"  MANCA {rel}: {explain}")
            return 1
        destination = os.path.join(outside, rel)
        if kind == "cartella":
            shutil.copytree(source, destination)
        else:
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination)
        included.append(rel)
        print(f"  {rel:16} {mb(weight(source)):>9}   {explain}")

    with open(os.path.join(outside, "synopsis.json"), "w", encoding="utf-8") as f:
        json.dump(synopsis(meta), f, ensure_ascii=False, indent=2)
    # lo stesso synopsis va anche nell'albero di lavoro, cosi' chi prova in
    # locale vede quello che vedranno gli altri
    with open(os.path.join(MOD, "synopsis.json"), "w", encoding="utf-8") as f:
        json.dump(synopsis(meta), f, ensure_ascii=False, indent=2)
    print(f"  {'synopsis.json':16} {mb(weight(os.path.join(outside, 'synopsis.json'))):>9}   "
          f"scritto da {os.path.relpath(META, PROJ)} (versione {version})")

    print("\n4. lasciato fuori")
    outside_entries = []
    for entry in sorted(os.listdir(MOD)):
        if entry in included or entry in GENERATED:
            continue
        if entry == "loc":                     # dentro c'e' loc_it, che e' incluso
            for below in sorted(os.listdir(os.path.join(MOD, "loc"))):
                if below != "loc_it":
                    outside_entries.append((f"loc/{below}", os.path.join(MOD, "loc", below),
                                       "riferimento per chi traduce"))
            continue
        explain = "istruzioni per un altro strumento" if entry == ".github" else ""
        outside_entries.append((entry, os.path.join(MOD, entry), explain))
    discarded = 0
    for name, path_for, explain in outside_entries:
        n = weight(path_for)
        discarded += n
        print(f"  {name:24} {mb(n):>9}   {explain}")
    print(f"  {'serapeum_catalogue_number.txt':24} {'-':>9}   lo scrive il gioco al primo caricamento")
    print(f"  in tutto {mb(discarded)} non pubblicati")

    if writes_zip:
        print("\n5. zip")
        with zipfile.ZipFile(final_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for dirpath, _, files in os.walk(outside):
                for f in sorted(files):
                    p = os.path.join(dirpath, f)
                    z.write(p, os.path.join(MOD_NAME, os.path.relpath(p, outside)))
        print(f"  {os.path.relpath(final_zip, PROJ)}  {mb(os.path.getsize(final_zip))}")

    print(f"\npacchetto: {mb(weight(outside))} in {os.path.relpath(outside, PROJ)}, "
          f"albero di lavoro: {mb(weight(MOD))}")
    print(f"file: {sum(len(f) for _, _, f in os.walk(outside))}")

    if "--install" in sys.argv:
        print("\n6. installo nel gioco")
        if not os.path.isdir(MODS):
            print(f"  la cartella dei mod non c'e': {MODS}")
            return 1
        destination = os.path.join(MODS, MOD_NAME)
        # Il numero di catalogo lo scrive il gioco quando carica il mod sul
        # Workshop la prima volta, e senza di lui il caricamento successivo
        # creerebbe un oggetto nuovo invece di aggiornare quello che c'e'.
        # Reinstallare non deve buttarlo via.
        catalogue = os.path.join(destination, "serapeum_catalogue_number.txt")
        saved = open(catalogue, encoding="utf-8").read() if os.path.exists(catalogue) else None
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.copytree(outside, destination)
        if saved is not None:
            with open(catalogue, "w", encoding="utf-8") as f:
                f.write(saved)
            print(f"  numero di catalogo conservato: {saved.strip()}")
        print(f"  {destination}")
        print("  nel gioco: Opzioni -> Mods, poi la lingua in Opzioni -> Lingua")
    return 0


if __name__ == "__main__":
    sys.exit(main())
