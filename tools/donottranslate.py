"""Richiesta 3: dove FR ed ES concordano nel NON tradurre -> glossario 'lasciare in inglese'."""
import re, collections, json
from bohloc import *

core,*_=load_tree(CORE); es,*_=load_tree(ES); fr,*_=load_tree(FR)

# --- A. stringhe intere lasciate identiche all'inglese da ENTRAMBI ---
both=[]; only_es=[]; only_fr=[]
for k,cv in core.items():
    for f,en in cv["strings"].items():
        e=es.get(k,{}).get("strings",{}).get(f)
        r=fr.get(k,{}).get("strings",{}).get(f)
        if not e or not r: continue
        se=e.strip()==en.strip(); sr=r.strip()==en.strip()
        if se and sr: both.append((k,f,en))
        elif se: only_es.append((k,f,en))
        elif sr: only_fr.append((k,f,en))
print(f"A. Stringhe lasciate in inglese da ENTRAMBI (FR+ES): {len(both)}")
print(f"   solo ES: {len(only_es)}   solo FR: {len(only_fr)}")
bycat=collections.Counter(k[0] for k,f,en in both)
print(f"   per categoria: {dict(bycat)}")
print("   campione (le piu' corte = nomi propri/termini):")
for k,f,en in sorted(both,key=lambda x:len(x[2]))[:30]:
    if en.strip(): print(f"      [{k[0]}/{k[1]}.{f}] {en[:70]!r}")

# --- B. termini che sopravvivono verbatim dentro i corpi tradotti ---
# candidati: label EN multi-maiuscola o nomi propri
cand=set()
for k,cv in core.items():
    lab=cv["strings"].get("label","").strip()
    if 3<=len(lab)<=40 and re.match(r"^[A-Z][A-Za-z' \-]+$", lab) and not lab.islower():
        cand.add(lab)
body_es=" \n".join(t for v in es.values() for t in v["strings"].values())
body_fr=" \n".join(t for v in fr.values() for t in v["strings"].values())
body_en=" \n".join(t for v in core.values() for t in v["strings"].values())
keep=[]
counts={}
for term in sorted(cand):
    n_en=body_en.count(term)
    if n_en<3: continue
    n_es=body_es.count(term); n_fr=body_fr.count(term)
    counts[term]=(n_en,n_es,n_fr)
    # sopravvive in entrambi in almeno meta' delle occorrenze inglesi
    if n_es>=max(2,n_en*0.5) and n_fr>=max(2,n_en*0.5):
        keep.append((term,n_en,n_es,n_fr))
keep.sort(key=lambda x:-x[1])
print(f"\nB. Termini che restano verbatim nei corpi FR *e* ES: {len(keep)}")
print(f"   {'termine':32} {'EN':>5} {'ES':>5} {'FR':>5}")
for t,a,b,c in keep[:45]:
    print(f"   {t:32} {a:5} {b:5} {c:5}")

# --- C. divergenze: uno traduce, l'altro no ---
div=[]
for term,(n_en,n_es,n_fr) in counts.items():
    if n_en<4: continue
    if (n_es>=n_en*0.5) != (n_fr>=n_en*0.5):
        div.append((term,n_en,n_es,n_fr))
div.sort(key=lambda x:-x[1])
print(f"\nC. Divergenze FR/ES (uno mantiene l'inglese, l'altro traduce): {len(div)} -> decisione nostra")
for t,a,b,c in div[:25]:
    who="ES mantiene, FR traduce" if b>c else "FR mantiene, ES traduce"
    print(f"   {t:32} EN{a:4} ES{b:4} FR{c:4}   {who}")

json.dump({"keep_both":[t for t,*_ in keep],"divergent":[t for t,*_ in div]},
          open("../docs/glossario-non-tradurre.json","w"),ensure_ascii=False,indent=1)
