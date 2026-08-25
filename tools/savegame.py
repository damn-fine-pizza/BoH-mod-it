"""Traduce le stringhe che il gioco ha gia' scritto dentro un salvataggio.

Il gioco non tiene tutti i testi nel compendio: quando istanzia una postazione
serializza nel salvataggio anche il suo `GoverningSphereSpec`, con dentro Label e
Description. Al caricamento la sfera viene ricreata da li', non dal compendio -
quindi in una partita cominciata prima dell'installazione del mod (o prima che
una certa stringa fosse tradotta) quel testo resta com'era.

E' cosi' che il bancone dell'Ufficio Postale continuava a leggersi «Post Office
Counter» in mezzo a una schermata italiana, mentre il file loc era tradotto: su
1447 sfere salvate, sei erano rimaste in inglese, ed erano esattamente le
postazioni del villaggio gia' visitate.

Una partita nuova non ha il problema. Questo strumento serve per quelle in corso.

Prudenza, perche' si tocca un salvataggio:
 - si sostituisce solo dove il valore inglese e' *esattamente* una chiave del
   dizionario, e solo nei campi Label, Description, Desc, StartDescription;
 - senza --apply non scrive niente, dice solo cosa cambierebbe;
 - con --apply salva prima una copia accanto, col suffisso .prima-della-traduzione.

Funziona anche al contrario. Chi torna all'inglese - per confrontare, per
segnalare un bug agli sviluppatori, per smettere di usare il mod - si ritrova le
stesse stringhe italiane incastrate nel salvataggio, e il gioco in inglese le
rilegge da li'. Con --to-english si rovescia il dizionario e si rimette
l'inglese. Il rovescio si costruisce solo dalle rese non ambigue: se due
stringhe inglesi diverse hanno la stessa resa italiana non si puo' sapere quale
rimettere, e quelle si lasciano stare.

Uso:
    python3 tools/savegame.py                   che cosa cambierebbe, in tutti i salvataggi
    python3 tools/savegame.py AUTOSAVE.json     solo quello
    python3 tools/savegame.py --apply           scrive, dopo aver fatto la copia
    python3 tools/savegame.py --to-english       rimette l'inglese (con --apply scrive)
"""
import json, os, shutil, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ, MODS

SAVES = os.path.dirname(MODS)          # la cartella del gioco, sopra mods/
DICT = os.path.join(PROJ, "translations", "it.json")
FIELDS = {"Label", "Description", "Desc", "StartDescription"}


def translate(node, d, count, examples):
    """Scende nel salvataggio e sostituisce i testi noti. Ritorna il nodo."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in FIELDS and isinstance(v, str) and v.strip():
                it = d.get(v.strip())
                if it and it != v:
                    node[k] = it
                    count[k] += 1
                    if len(examples) < 12:
                        examples.append((k, v[:70], it[:70]))
                    continue
            translate(v, d, count, examples)
    elif isinstance(node, list):
        for x in node:
            translate(x, d, count, examples)
    return node


def reverse(strings):
    """{italiano: inglese}, ma solo dove la resa e' di una stringa sola.

    Il dizionario non e' iniettivo: «Enquire» e «Investigate» possono finire
    tutt'e due su «Indaga». Rimettere l'inglese a indovinare sarebbe peggio del
    problema che si vuole risolvere, quindi le rese usate piu' di una volta si
    lasciano in italiano.
    """
    quante = collections.Counter(v.strip() for v in strings.values() if v.strip())
    return {v.strip(): k for k, v in strings.items()
            if v.strip() and quante[v.strip()] == 1 and v.strip() != k.strip()}


def main():
    apply_fixes = "--apply" in sys.argv
    to_english = "--to-english" in sys.argv
    chosen_ones = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = json.load(open(DICT, encoding="utf-8"))["strings"]
    if to_english:
        d = reverse(d)
    if not os.path.isdir(SAVES):
        print(f"cartella dei salvataggi non trovata: {SAVES}")
        return 1
    file = sorted(f for f in os.listdir(SAVES)
                  if f.endswith(".json") and f not in ("achievements.json", "beta.json",
                                                       "RemoteConfigCache.json"))
    if chosen_ones:
        file = [f for f in file if f in chosen_ones]
    if not file:
        print("nessun salvataggio da esaminare")
        return 1
    total = 0
    for f in file:
        p = os.path.join(SAVES, f)
        try:
            with open(p, encoding="utf-8") as h:
                data = json.load(h)
        except Exception as e:
            print(f"  {f}: non e' un salvataggio leggibile ({str(e)[:60]})")
            continue
        count, examples = collections.Counter(), []
        translate(data, d, count, examples)
        n = sum(count.values())
        total += n
        verso = "da rimettere in inglese" if to_english else "da tradurre"
        print(f"\n{f}  ({os.path.getsize(p)/1024/1024:.1f} MB): {n} testi {verso}"
              f"{'  ' + ', '.join(f'{k} {v}' for k, v in count.most_common()) if n else ''}")
        for field, before, after in examples:
            print(f"    {field:12} {before!r}\n    {'':12} -> {after!r}")
        if n and apply_fixes:
            copy_of = p + (".prima-dell-inglese" if to_english else ".prima-della-traduzione")
            if not os.path.exists(copy_of):
                shutil.copy2(p, copy_of)
            with open(p, "w", encoding="utf-8") as h:
                json.dump(data, h, ensure_ascii=False, indent=2)
            print(f"    scritto; copia di sicurezza in {os.path.basename(copy_of)}")
    if total and not apply_fixes:
        print(f"\n{total} testi in tutto. Con --apply li scrivo, dopo aver fatto una copia.")
    elif not total:
        print("\nniente da fare: i salvataggi sono gia' allineati al dizionario")
    return 0


if __name__ == "__main__":
    sys.exit(main())
