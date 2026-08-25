"""Riporta i titoli dei libri alla sola forma italiana.

Fino a un certo punto il progetto ha seguito il mod francese, che tiene il
titolo inglese e affianca la traduzione fra parentesi -- The Sun's Design
(Il Disegno del Sole) -- perche' le copertine portano impresse le iniziali del
titolo inglese e tradurlo le renderebbe false.

Quel vincolo non c'e' piu': le copertine le ridisegniamo. E allora la forma
francese risolve un problema che non abbiamo, al prezzo di raddoppiare
l'etichetta e di far ordinare la biblioteca in inglese mentre chi gioca pensa
in italiano. Tutte e tre le localizzazioni ufficiali, e anche lo spagnolo,
traducono il titolo e basta; il francese affianca l'inglese solo perche' non ha
rifatto le immagini.

Cio' che segue le parentesi -- la qualificazione e il numero di volume -- resta:
  «The Three and the Three (I Tre e i Tre) - Manoscritto di Kerisham»
    -> «I Tre e i Tre - Manoscritto di Kerisham»
  «Travelling at Night (Viaggiare di Notte), vol 1»
    -> «Viaggiare di Notte, vol 1»

Sostituisce booktitles.py, che componeva la forma francese e non serve piu'.

Uso: python titles.py [--write]
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ
from booktitles import book_titles

DICT = os.path.join(PROJ, "translations", "it.json")


def disassemble(value, english):
    """«EN (IT) - Qual, vol N» -> «IT - Qual, vol N». None se non e' composto."""
    m = re.match(r"^(.*?)\s*\((.+?)\)\s*(.*)$", value)
    if not m:
        return None
    head, it, tail = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    # la testa dev'essere il titolo inglese, altrimenti quelle parentesi fanno
    # parte del titolo italiano e non vanno toccate. Il confronto ignora il
    # suffisso di volume, che nell'inglese c'e' e nella testa no.
    expected_value = re.sub(r",?\s*(?:vol\.?|book)\s*\d+\s*$", "", english, flags=re.I).strip()
    expected_value = re.split(r"\s*\(", expected_value)[0].strip()
    # l'apostrofo va normalizzato prima di confrontare: l'inglese ha quello
    # dritto, la nostra resa quello tipografico, e The Sun's Design non
    # combaciava con The Sun’s Design
    norm = lambda t: t.replace("’", "'").replace("‘", "'")
    if norm(head) != norm(expected_value):
        return None
    # la coda si attacca senza spazio se comincia per punteggiatura
    if not tail:
        return it
    return it + ("" if tail[0] in ",;:" else " ") + tail


def main(write=False):
    d = json.load(open(DICT, encoding="utf-8"))
    titles = book_titles()
    done_ones, unchanged, absent = [], 0, 0
    for en in sorted(titles):
        it = d["strings"].get(en)
        if it is None:
            absent += 1
            continue
        fresh_one = disassemble(it, en)
        if fresh_one is None or fresh_one == it:
            unchanged += 1
            continue
        done_ones.append((en, it, fresh_one))
        if write:
            d["strings"][en] = fresh_one
    print(f"titoli: {len(titles)}   da smontare: {len(done_ones)}   "
          f"gia' a posto: {unchanged}   non tradotti: {absent}")
    for en, old_one, fresh_one in done_ones[:8]:
        print(f"   {old_one[:60]!r}\n     -> {fresh_one[:60]!r}")
    if write:
        import tempfile
        t = tempfile.NamedTemporaryFile("w", encoding="utf-8",
                                        dir=os.path.dirname(DICT), delete=False, suffix=".tmp")
        json.dump(d, t, ensure_ascii=False, indent=1, sort_keys=True)
        t.close()
        os.replace(t.name, DICT)
        print(f"\ndizionario aggiornato: {len(done_ones)} titoli")


if __name__ == "__main__":
    main("--write" in sys.argv)
