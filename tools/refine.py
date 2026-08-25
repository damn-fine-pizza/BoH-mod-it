"""Raffinamento: confini di parola sui termini gia' selezionati + cosa fa ES coi termini di lore."""
import re, json
from bohloc import *
core,*_=load_tree(CORE); es,*_=load_tree(ES); fr,*_=load_tree(FR)
body_es=" \n".join(t for v in es.values() for t in v["strings"].values())
body_fr=" \n".join(t for v in fr.values() for t in v["strings"].values())
body_en=" \n".join(t for v in core.values() for t in v["strings"].values())
g=json.load(open("../docs/glossario-non-tradurre.json"))
def c(term, body):
    return len(re.findall(r"(?<![\w])"+re.escape(term)+r"(?![\w])", body))
print("=== B raffinato: termini identici in EN, ES e FR (confini di parola) ===")
solid=[]
for t in g["keep_both"]:
    a,b,d=c(t,body_en),c(t,body_es),c(t,body_fr)
    if a>=3 and b>=max(2,a*0.5) and d>=max(2,a*0.5):
        solid.append((a,t,b,d))
    elif a>=3:
        print(f"   SCARTATO (falso positivo): {t:24} EN{a:4} ES{b:4} FR{d:4}")
solid.sort(reverse=True)
print(f"\n   confermati: {len(solid)}")
for a,t,b,d in solid: print(f"   {t:30} EN{a:4} ES{b:4} FR{d:4}")

print("\n=== termini di lore: cosa ne fa lo spagnolo ===")
LORE=["Ereb","Fet","Phost","Shapt","Trist","Chor","Wist","Mettle","Perinculate","Fucine",
      "Carapace","Nectar","Illumination","Horomachistry","Hushery","Bosk","Birdsong",
      "Skolekosophy","Preservation","Ithastry","Nyctodromy"]
for t in LORE:
    k=("elements",t.lower()); k2=("elements","w."+t.lower())
    src=core.get(k) or core.get(k2)
    if src:
        key=k if k in core else k2
        print(f"   {t:16} label EN={core[key]['strings'].get('label','-'):22} ES={es.get(key,{}).get('strings',{}).get('label','-'):22} FR={fr.get(key,{}).get('strings',{}).get('label','-')}")
    else:
        print(f"   {t:16} (nessuna entita' omonima) corpi: EN{c(t,body_en):4} ES{c(t,body_es):4} FR{c(t,body_fr):4}")
