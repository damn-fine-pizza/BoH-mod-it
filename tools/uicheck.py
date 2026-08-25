"""Richiesta 1: integrita' tag/token e lunghezze sulle UI labels (culture.json)."""
import re, os, os, collections
from bohloc import read, CULTURE_EN, CULTURE_ES, CULTURE_IT, IT_INSTALLED

TAG=re.compile(r"<[^<>\n]{1,40}>")
TOKEN=re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
EN=os.path.join(CULTURE_EN,"en","culture.json")
ITC=CULTURE_IT
ESC=CULTURE_ES
FRC=None
for base in [os.path.join(os.path.dirname(IT_INSTALLED),"_mod_in_french")]:
    for r,d,f in os.walk(os.path.dirname(base)):
        for fn in f:
            if fn.endswith(".json") and "french" in r.lower() and "culture" in fn.lower():
                FRC=os.path.join(r,fn)

def ui(p):
    return read(p)["cultures"][0].get("uilabels",{})

def visible(s):
    s=TAG.sub("", s)
    s=TOKEN.sub("", s)
    s=s.replace("$","").replace("[","").replace("]","")
    return " ".join(s.split())

en=ui(EN); it=ui(ITC); es=ui(ESC)
fr=ui(FRC) if FRC else {}
print(f"UI labels: EN {len(en)} | IT {len(it)} | ES {len(es)} | FR {len(fr) if fr else 'n/d'}\n")

print("--- chiavi IT inesistenti in EN (label morte: il gioco ricade sull'inglese) ---")
dead=[k for k in it if k not in en]
for k in dead: print(f"   {k}: {it[k][:70]!r}")
print(f"   totale: {len(dead)}\n")

print("--- chiavi EN assenti in IT (ricadono sull'inglese in gioco) ---")
miss=[k for k in en if k not in it]
for k in miss: print(f"   {k}: EN={en[k][:60]!r}  ES={'presente' if k in es else 'assente anche in ES'}")
print(f"   totale: {len(miss)}\n")

print("--- integrita' tag/token IT vs EN ---")
prob=collections.Counter(); ex=collections.defaultdict(list)
for k,v in en.items():
    t=it.get(k)
    if t is None or t.strip()==v.strip(): continue
    if collections.Counter(TAG.findall(v))!=collections.Counter(TAG.findall(t)):
        prob["tag alterati"]+=1; ex["tag alterati"].append((k,v,t))
    if set(TOKEN.findall(v))!=set(TOKEN.findall(t)):
        prob["token {SETTING} alterati"]+=1; ex["token {SETTING} alterati"].append((k,v,t))
    if v.startswith("$")!=t.startswith("$"):
        prob["prefisso $ perso/aggiunto"]+=1; ex["prefisso $ perso/aggiunto"].append((k,v,t))
    if v.count("\n")!=t.count("\n"):
        prob["a-capo diversi"]+=1; ex["a-capo diversi"].append((k,v,t))
checked=sum(1 for k,v in en.items() if it.get(k) and it[k].strip()!=v.strip())
print(f"   stringhe effettivamente controllate: {checked}/{len(en)}")
if not prob: print("   nessun problema di tag/token")
for p,n in prob.most_common():
    print(f"   {p}: {n}")
    for k,v,t in ex[p][:3]:
        print(f"      {k}\n        EN: {v[:100]!r}\n        IT: {t[:100]!r}")

print("\n--- lunghezze visibili (testo che finisce nei pulsanti) ---")
rows=[]
for k,v in en.items():
    if k not in it: continue
    ve,vi=visible(v),visible(it[k])
    if not ve or vi==ve: continue
    ratio=len(vi)/len(ve)
    vs=visible(es.get(k,"")) if k in es else None
    rows.append((ratio,k,ve,vi,vs))
rows.sort(reverse=True)
over=[r for r in rows if r[0]>1.3]
print(f"   label IT piu' lunghe di EN oltre il 30%: {len(over)}/{len(rows)}")
for ratio,k,ve,vi,vs in over[:14]:
    s=f" | ES {len(vs):>2}c {vs!r}" if vs else ""
    print(f"   x{ratio:.2f}  {k}\n        EN {len(ve):>2}c {ve!r}\n        IT {len(vi):>2}c {vi!r}{s}")
import statistics
print(f"\n   rapporto medio IT/EN: {statistics.mean(r[0] for r in rows):.2f}")
if es:
    er=[len(visible(es[k]))/max(1,len(visible(en[k]))) for k in en if k in es and visible(en[k]) and visible(es[k])!=visible(en[k])]
    print(f"   rapporto medio ES/EN: {statistics.mean(er):.2f}  (riferimento)")
