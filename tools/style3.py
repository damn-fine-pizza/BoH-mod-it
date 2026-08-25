"""Label di due parole: il classificatore precedente le saltava (serviva len(rest)>=2)."""
import re, os
from bohloc import read, CULTURE_EN, CULTURE_ES, CULTURE_IT
B=CULTURE_EN
ITC=CULTURE_IT
ESC=CULTURE_ES
TAG=re.compile(r"<[^<>\n]{1,40}>"); TOKEN=re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
def ui(p): return read(p)["cultures"][0]["uilabels"]
def vis(s):
    s=TAG.sub("",s); s=TOKEN.sub("",s)
    return " ".join(s.replace("$","").replace("[","").replace("]","").split())
def words(t): return re.findall(r"[A-Za-zÀ-ÿ’']+", t)
en,it,es=ui(f"{B}/en/culture.json"),ui(ITC),ui(ESC)
cand=[]
for k,v in it.items():
    w=words(vis(v))
    rest=[x for x in w[1:] if len(x)>2]
    if len(rest)!=1: continue
    if not rest[0][0].isupper(): continue
    if rest[0].isupper(): continue
    ev=vis(es.get(k,"")); we=[x for x in words(ev)[1:] if len(x)>2]
    es_cap = bool(we) and all(x[0].isupper() for x in we)
    cand.append((k,vis(v),ev,es_cap))
print(f"label italiane a due parole con la seconda maiuscola: {len(cand)}")
print("\n-- ES capitalizza allo stesso modo => nome proprio, si lascia --")
for k,i,e,c in cand:
    if c: print(f"   {k:32} IT {i!r:36} ES {e!r}")
print("\n-- ES non capitalizza => anglicismo, da correggere --")
fix=[(k,i,e) for k,i,e,c in cand if not c]
for k,i,e in fix: print(f"   {k:32} IT {i!r:36} ES {e!r}")
print(f"\ntotale da correggere: {len(fix)}")
