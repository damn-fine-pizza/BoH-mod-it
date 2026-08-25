"""Richiesta 2: qualita'/consistenza ortotipografica delle UI labels IT, con ES come metro."""
import re, collections
from bohloc import read, CULTURE_EN, CULTURE_ES, CULTURE_IT
import os
EN=os.path.join(CULTURE_EN,"en","culture.json")
# l'albero di lavoro, non la copia installata: e' la fonte, e non puo' essere
# vecchia di un'installazione.
ITC=CULTURE_IT
ESC=CULTURE_ES
TAG=re.compile(r"<[^<>\n]{1,40}>"); TOKEN=re.compile(r"\{[A-Z]+:[a-zA-Z0-9_.]+\}")
def ui(p): return read(p)["cultures"][0]["uilabels"]
def vis(s):
    s=TAG.sub("",s); s=TOKEN.sub("",s)
    return " ".join(s.replace("$","").replace("[","").replace("]","").split())
en,it,es=ui(EN),ui(ITC),ui(ESC)

def titlecase_ratio(d, name):
    tc=[]; sc=[]
    for k,v in d.items():
        t=vis(v)
        words=[w for w in re.findall(r"[A-Za-zÀ-ÿ']+", t) if len(w)>3]
        if len(words)<2: continue
        cap=sum(1 for w in words[1:] if w[0].isupper())
        if cap==len(words)-1: tc.append((k,t))
        elif cap==0: sc.append((k,t))
    print(f"{name}: {len(tc)} label in Title Case anglosassone, {len(sc)} in stile frase (su {len(tc)+len(sc)} valutabili)")
    return tc,sc
print("=== maiuscole nei titoli (in italiano il Title Case inglese e' un anglicismo) ===")
tc_it,_=titlecase_ratio(it,"IT")
tc_es,_=titlecase_ratio(es,"ES")
print("\n   esempi IT in Title Case (con resa ES per confronto):")
for k,t in tc_it[:14]:
    print(f"      {k}\n         IT: {t!r}\n         ES: {vis(es.get(k,'-'))!r}")

print("\n=== apostrofi: dritto (') vs tipografico (’) ===")
for name,d in (("IT",it),("ES",es)):
    straight=[k for k,v in d.items() if "'" in vis(v)]
    curly=[k for k,v in d.items() if "’" in vis(v)]
    print(f"   {name}: {len(straight)} label con ' dritto, {len(curly)} con ’ tipografico")
    if name=="IT":
        print(f"      dritto: {[vis(it[k]) for k in straight[:6]]}")
        print(f"      curvo : {[vis(it[k]) for k in curly[:6]]}")

print("\n=== virgolette ===")
for name,d in (("EN",en),("IT",it),("ES",es)):
    q=collections.Counter()
    for v in d.values():
        t=vis(v)
        for ch,lab in (("'","apostrofo/virgoletta dritta"),('"','doppia dritta'),("«","caporali"),("“","doppia curva")):
            if ch in t: q[lab]+=1
    print(f"   {name}: {dict(q)}")

print("\n=== accenti sbagliati (E' invece di E', o vocali senza accento) ===")
bad=[(k,vis(v)) for k,v in it.items() if re.search(r"\bE'|\bpo'\B|perche\b|piu\b|gia\b|cosi\b|puo\b", vis(v))]
print(f"   IT: {len(bad)} occorrenze")
for k,t in bad[:10]: print(f"      {k}: {t!r}")
