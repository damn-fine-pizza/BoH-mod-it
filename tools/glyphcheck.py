"""Ogni carattere usato dall'italiano e' garantito nell'atlante del font?

core/_core.txt e' l'elenco dei code point che Weather Factory compila
nell'atlante per il contenuto inglese, reso con fontscript 'latin'. E' la
fonte autorevole: piu' affidabile che contare le occorrenze nel testo,
perche' include anche i caratteri usati in punti che l'estrazione non copre.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import read, load_tree, CORE, MOD

ATLAS = os.path.join(CORE, "_core.txt")
allowed = {int(x) for x in open(ATLAS).read().split(",") if x.strip().isdigit()}

text = "".join(read(os.path.join(MOD, "content", "cultures", "culture.json"))
                ["cultures"][0]["uilabels"].values())
loc = os.path.join(MOD, "loc", "loc_it")
if os.path.isdir(loc):
    idx, *_ = load_tree(loc)
    text += "".join(t for v in idx.values() for t in v["strings"].values())

missing = sorted({c for c in text if ord(c) not in allowed})
print(f"atlante: {len(allowed)} code point | testo italiano: {len(set(text))} caratteri distinti")
if missing:
    print("\nCARATTERI NON NELL'ATLANTE (rischio tofu):")
    for c in missing:
        print(f"   {c!r}  U+{ord(c):04X}")
else:
    print("\nnessun carattere fuori dall'atlante")
sys.exit(1 if missing else 0)
