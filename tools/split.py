"""Divide le stringhe ancora da tradurre in slice, una per agente.

La partizione e' per stringa distinta, non per file: la stessa frase inglese
ricorre in piu' file (\"Memory\" 669 volte) e due agenti la renderebbero in modo
diverso, che e' esattamente la consistenza che stiamo cercando di garantire.

Le slice gia' distribuite non sono ancora nel dizionario finche' non le si
fonde, quindi per generare il giro successivo serve un offset: senza, si
riassegnerebbero le stesse stringhe a un altro agente.

Uso: python split.py <n_agenti> <stringhe_per_agente> [--offset N] [--from M]
     --offset  salta le prime N stringhe (gia' assegnate a un giro precedente)
     --from      numera i file a partire da chunk_M.json
"""
import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import pending, prio, PRIORITY
from bohloc import PROJ

# note interne di sviluppo: il kit dice che non vanno tradotte
SKIP = re.compile(r"recipe aspect|no loc needed|NO NEED TO LOCALISE|Recipe meta|"
                  r"marker aspect|likely candidate for renaming|xtrigger|Xtrigger|"
                  r"HIDDEN ASPECT|offstage|can go here|deck draw|suitabiliser", re.I)

def main(n_agents, per_agent, offset=0, first=1):
    byt = pending()
    sorted_ones = sorted(byt.items(), key=lambda kv: (prio(kv[1][0][0]), kv[1][0][0], kv[0]))
    todo = [(t, occ) for t, occ in sorted_ones if not SKIP.search(t) and len(t.strip()) > 1]
    skipped = len(sorted_ones) - len(todo)

    todo = todo[offset:]
    out = os.path.join(PROJ, "translations", "parts")
    os.makedirs(out, exist_ok=True)
    tot = 0
    for i in range(n_agents):
        slice = todo[i*per_agent:(i+1)*per_agent]
        if not slice:
            break
        p = os.path.join(out, f"chunk_{first+i}.json")
        json.dump([{"en": t, "dove": occ[0][1], "ricorre": len(occ)} for t, occ in slice],
                  open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        words = sum(len(t.split()) for t, _ in slice)
        print(f"chunk_{first+i}.json: {len(slice)} stringhe, {words} parole")
        tot += len(slice)
    print(f"\ntotale distribuito: {tot}   note interne saltate: {skipped}   "
          f"ancora in coda: {len(todo)-tot}")

if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(name, dflt):
        return int(a[a.index(name)+1]) if name in a else dflt
    pos = [x for x in a if not x.startswith("--") and
           (a.index(x) == 0 or not a[a.index(x)-1].startswith("--"))]
    main(int(pos[0]) if pos else 5, int(pos[1]) if len(pos) > 1 else 400,
         opt("--offset", 0), opt("--from", 1))
