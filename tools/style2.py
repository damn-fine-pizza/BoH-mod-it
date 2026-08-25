"""Title Case senza il bias del filtro sulle parole corte, e al netto dei nomi propri."""
import re, os
from bohloc import read, CULTURE_EN, CULTURE_ES, CULTURE_IT
B=CULTURE_EN
ITC=CULTURE_IT
ESC=CULTURE_ES
TAG=re.compile(r"<[^<>\n]{1,40}>"); TOKEN=re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
def ui(p): return read(p)["cultures"][0].get("uilabels",{})
def vis(s):
    s=TAG.sub("",s); s=TOKEN.sub("",s)
    return " ".join(s.replace("$","").replace("[","").replace("]","").split())
en,it,es=ui(f"{B}/en/culture.json"),ui(ITC),ui(ESC)

def words(t):
    return re.findall(r"[A-Za-zÀ-ÿ’']+", t)

def classify(d):
    """Title Case = tutte le parole dopo la prima iniziano maiuscole (escluse quelle di 1-2 lettere)."""
    tc=[]; sc=[]
    for k,v in d.items():
        w=words(vis(v))
        if len(w)<3: continue           # serve almeno prima + 2 successive
        rest=[x for x in w[1:] if len(x)>2]
        if len(rest)<2: continue
        cap=sum(1 for x in rest if x[0].isupper())
        if cap==len(rest): tc.append(k)
        elif cap==0: sc.append(k)
    return tc,sc

tc_it,sc_it=classify(it); tc_es,sc_es=classify(es)
print(f"Title Case (metodo corretto)  IT: {len(tc_it)} TC / {len(sc_it)} frase")
print(f"                              ES: {len(tc_es)} TC / {len(sc_es)} frase\n")

print("--- al netto dei nomi propri: label IT in TC dove ES NON capitalizza le stesse parole ---")
real=[]
for k in tc_it:
    if k not in es: continue
    we=[x for x in words(vis(es[k]))[1:] if len(x)>2]
    if not we: continue
    if sum(1 for x in we if x[0].isupper())==len(we):
        continue                      # anche ES capitalizza -> nomi propri, non anglicismo
    real.append(k)
print(f"anglicismo di stile confermato: {len(real)} label su {len(tc_it)}")
for k in real:
    print(f"   {k:32} IT {vis(it[k])!r:42} ES {vis(es[k])!r}")

print("\n--- chiavi 'morte' IT: presenti nelle localizzazioni ufficiali? ---")
dead=[k for k in it if k not in en]
import os
for cult in ["ru","jp","zh-hans"]:
    p=f"{B}/{cult}/culture.json"
    if not os.path.exists(p): continue
    u=ui(p)
    print(f"   {cult}: " + ", ".join(f"{k}={'SI' if k in u else 'no'}" for k in dead))
print(f"   en: " + ", ".join(f"{k}={'SI' if k in en else 'no'}" for k in dead))
