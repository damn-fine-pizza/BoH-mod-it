"""Ricompone una slice dai frammenti incrementali.

Il briefing chiedeva di riscrivere part_N.json ogni quaranta stringhe, per non
perdere il lavoro e per rendere visibile l'avanzamento. Funziona, ma fa pagare
il tradotto molte volte: a fine slice il file pesa un centinaio di kilobyte e
riscriverlo dieci volte significa emetterlo dieci volte. L'output e' la parte
cara.

Qui ogni salvataggio e' invece un frammento con le sole stringhe nuove --
part_N.001.json, part_N.002.json, ... -- e alla fine si ricompongono. Stesso
lavoro salvato, stessa visibilita', un quinto dei token in uscita.

In caso di sovrapposizione vince il frammento piu' recente: un ripensamento si
esprime riscrivendo la coppia in un frammento successivo.

I frammenti fusi non si cancellano: si archiviano in parts/fatti/. Costa nulla
e serve. Una slice e' stata persa perche' dopo l'unione qualcuno ha riscritto
part_N.json con un decimo delle coppie, e senza i frammenti non c'era piu'
niente da cui ricomporla.

Uso: python join.py 6
     python join.py 6 --archive    ricompone dai frammenti archiviati
"""
import json, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ

PARTS = os.path.join(PROJ, "translations", "parts")


DONE = os.path.join(PARTS, "fatti")


def fragments(n, where=None):
    return sorted(glob.glob(os.path.join(where or PARTS, f"part_{n}.[0-9]*.json")))


def join_parts(n, archive=True, where=None):
    pieces = fragments(n, where)
    dest = os.path.join(PARTS, f"part_{n}.json")
    merged = {}
    if os.path.exists(dest):
        try:
            merged = json.load(open(dest, encoding="utf-8"))
        except Exception:
            merged = {}
    read_count = 0
    for p in pieces:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  {os.path.basename(p)}: JSON illeggibile, saltato ({str(e)[:60]})")
            continue
        merged.update(d)
        read_count += 1
    json.dump(merged, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if archive and where is None:
        os.makedirs(DONE, exist_ok=True)
        for p in pieces:
            os.replace(p, os.path.join(DONE, os.path.basename(p)))
    print(f"part_{n}.json: {len(merged)} coppie da {read_count} frammenti")
    return len(merged)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    where = DONE if "--archive" in sys.argv else None
    for n in a or ["1"]:
        join_parts(int(n), where=where)
