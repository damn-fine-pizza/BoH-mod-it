"""Controlla una slice appena tradotta, prima che rientri nel dizionario.

Serve a chi traduce: gli stessi controlli che validate.py fa sul dizionario,
piu' i tre che valgono solo per una slice -- le chiavi che non combaciano con
l'inglese ricevuto (la traduzione andrebbe persa in silenzio al momento della
fusione), le stringhe assegnate ma non consegnate, e le rese rimaste in
inglese.

Non tutte le stringhe mancanti sono un errore: le note interne di sviluppo e gli
identificatori vanno omessi apposta. Per questo qui si elencano, non si contano
come problemi.

Uso: python checkpart.py 6
     python checkpart.py --dictionary     lo stesso controllo su it.json
"""
import json, os, sys, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ
from validate import analyze, show_report, load_rules, TAG, TOKEN

PARTS = os.path.join(PROJ, "translations", "parts")
DICT = os.path.join(PROJ, "translations", "it.json")
# Le stringhe che restano in inglese per scelta verificata: le tiene
# identical.py, e le legge anche questo controllo. Senza, i diciassette titoli
# della colonna sonora - musica che esiste davvero, e i titoli delle opere reali
# non si traducono - farebbero fallire il cancello a ogni giro, e l'unico modo
# di chiuderlo sarebbe tradurli, cioe' sbagliare.
INTENDED = os.path.join(PROJ, "translations", "identiche-volute.json")


def intended():
    try:
        return {k for k in json.load(open(INTENDED, encoding="utf-8")) if not k.startswith("_")}
    except Exception:
        return set()

# --- stringhe rimaste in inglese -------------------------------------------
# Nessun altro controllo le vedeva: una resa "italiana" identica all'originale
# ha le chiavi giuste, il markup giusto, i glifi giusti, e passa. E' il modo in
# cui una slice tradotta male entra nel dizionario senza che nulla protesti.
#
# Il segnale piu' netto non e' la somiglianza generica ma la grammatica: le
# parole funzionali inglesi non esistono in italiano. Due di queste dentro una
# resa e la frase e' rimasta in inglese, comunque la si misuri. Sono escluse
# apposta le forme che collidono con l'italiano -- in, me, no, so, do, or, all,
# come, mine, more, note -- che darebbero falsi positivi su testo italiano
# corretto ("Blackberries" -> "More" e' una resa giusta, non una resa mancata).
STOP_EN = frozenset("""
of to it is be he we us my if up at by as an am on the and are was were that
this these those with for from its his her hers she him you your yours they
them their there then than our ours not but who what when where which whom
whose have has had been being will would shall should can could may might must
does did doing done about after before over under through between against
without within upon while because though although yet still even never always
very much many most own same too also just now here how why any each few nor
other others only such like out into one across along among behind beneath
beside beyond during except inside outside since toward towards until unless
whether whatever whenever wherever whoever else ever everything nothing
something anything someone everyone anyone nobody somebody itself himself
herself themselves myself ourselves yourself
""".split())

# Un titolo in latino resta invariato per convenzione (convenzioni.md, 5-ter):
# la coincidenza con l'originale e' voluta e non va segnalata.
LATIN_FUNCTION_WORDS = frozenset("de ad ex et per sub cum sine contra super pro post ante "
                     "atque nec vel aut qui quae quod non licet sic hic ubi quo "
                     "tibi mihi sibi nobis vobis est sunt esse nihil omnia "
                     "semper nunc tunc autem enim ergo igitur tamen etiam quam "
                     "quid quis cur ita iam sed nam".split())
LATIN_ENDINGS = ("us", "um", "is", "ae", "orum", "arum", "ibus", "ium", "tio", "tas",
            "atum", "ensis")
# particelle dei nomi composti: minuscole, ma il nome resta un nome
PARTICLES = frozenset("van von de del della di da du des le la den ter mac ap "
                       "bin ibn al el".split())
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}")
# In italiano una parola seguita da apostrofo e' un'elisione o un troncamento --
# dell’, un’, po’, be’ -- ed e' un segno di italiano, non di inglese. Senza
# questo, "be’" (per «bene») veniva contato come la parola inglese "be".
TRUNCATE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}(?=[’'])")
ASPECT = re.compile(r"[@#][a-z0-9_.]*\|")


def _words(s):
    """Le parole vere: via i tag, i token e gli id degli aspetti nei template."""
    s = ASPECT.sub(" ", TOKEN.sub(" ", TAG.sub(" ", str(s))))
    return WORD.findall(s)


def _proper_nouns(en):
    """Parole con l'iniziale maiuscola in mezzo a una frase: nomi propri, che
    restano in inglese per convenzione e non contano come mancata resa."""
    outside = set()
    for sentence in re.split(r"[.!?\n:;]", en):
        for p in _words(sentence)[1:]:
            if p[0].isupper():
                outside.add(p.lower())
    return outside


def _exempt(pen, exempt):
    """L'inglese e' un nome, un titolo latino, un elenco di nomi o pura
    punteggiatura: qui la resa italiana coincide legittimamente."""
    if not pen:
        return True                                   # punteggiatura, cifre, solo markup
    low = [p.lower() for p in pen]
    if any(p in STOP_EN for p in low):
        return False                                  # ha grammatica inglese: e' prosa
    if all(p in exempt for p in low):
        return True                                   # solo termini del glossario
    latin_count = sum(1 for p in low
              if p in LATIN_FUNCTION_WORDS or (len(p) >= 4 and p.endswith(LATIN_ENDINGS)))
    if latin_count * 2 >= len(low):
        return True                                   # titolo latino
    if all(p.isupper() for p in pen):
        return False    # tutto maiuscolo: e' una scelta grafica e non dice
                        # nulla sul fatto che sia un nome. EXPERIMENT BEYOND
                        # SIGHT e' il titolo di un film, e va tradotto.
    return len(pen) >= 2 and all(p[0].isupper() or p.lower() in PARTICLES
                                 for p in pen)


def _split_title(en, it):
    """Nella forma decisa per i libri -- The Sun's Design (Il Disegno del Sole)
    -- la parte inglese e' voluta: si guarda solo cio' che sta fra parentesi."""
    if it.startswith(en) and len(it) > len(en) + 2:
        rest = it[len(en):].lstrip()
        if rest.startswith("("):
            return rest
    return it


def untranslated(pairs, never):
    """Coppie dove l'italiano e' troppo vicino all'inglese.

    Ritorna (certe, sospette). Certe: la resa conserva la grammatica inglese,
    ripete l'originale parola per parola, o ne riusa piu' dei due terzi.
    Sospette: coincide con l'originale ma l'originale e' cosi' corto che la
    coincidenza puo' essere voluta -- si elencano, non bloccano.
    """
    exempt = {p.lower() for t in never for p in _words(t)}
    discard = sorted(never, key=len, reverse=True)
    certain, suspect = [], []
    for en, it in pairs:
        pen = _words(en)
        if _exempt(pen, exempt):
            continue
        bare = _split_title(en, str(it))
        for t in discard:              # i termini che restano in inglese per
            bare = bare.replace(t, " ")   # convenzione non sono un indizio
        pictorial_count = [p.lower() for p in _words(bare)]
        # scala dal conteggio le forme tronche italiane: "be’" non e' "be"
        truncated = collections.Counter(q.lower() for q in TRUNCATE.findall(bare))
        stop = 0
        for q in pictorial_count:
            if q not in STOP_EN:
                continue
            if truncated[q]:
                truncated[q] -= 1
            else:
                stop += 1
        equal = [p.lower() for p in pen] == pictorial_count
        # le parole dell'inglese che dovevano cambiare, e quante non l'hanno
        # fatto: fuori i nomi propri e i termini che restano per convenzione
        proper_nouns = _proper_nouns(en) | PARTICLES
        rendering = [p for p in (q.lower() for q in pen)
                if p not in exempt and p not in proper_nouns]
        # conta le parole distinte: una risata ripetuta ("Hee hee hee") non e'
        # dieci indizi, ne' e' una traduzione mancata
        distinct = set(rendering)
        share = sum(1 for p in distinct if p in pictorial_count) / len(distinct) if distinct else 0.0
        if (stop >= 2 or (stop and len(pictorial_count) <= 4)
                or (equal and len(distinct) >= 3)
                or (len(distinct) >= 3 and share >= 0.7)):
            certain.append((en, it))
        elif equal or (len(distinct) >= 3 and share >= 0.5):
            suspect.append((en, it))
    return certain, suspect


def show_english(certain, suspect, how_many=8):
    if certain:
        print(f"\nRESE RIMASTE IN INGLESE: {len(certain)}")
        print("  (la traduzione ripete l'originale: va rifatta prima della fusione)")
        for en, it in certain[:how_many]:
            print(f"      EN {en[:100]!r}\n      IT {str(it)[:100]!r}")
        if len(certain) > how_many:
            print(f"      ... e altre {len(certain) - how_many}")
    if suspect:
        print(f"\nmolto simili all'inglese (verifica che sia voluto): {len(suspect)}")
        for en, it in suspect[:5]:
            print(f"      EN {en[:100]!r}\n      IT {str(it)[:100]!r}")
        if len(suspect) > 5:
            print(f"      ... e altre {len(suspect) - 5}")


def main(n):
    cp = os.path.join(PARTS, f"chunk_{n}.json")
    pp = os.path.join(PARTS, f"part_{n}.json")
    if not os.path.exists(cp):
        print(f"chunk_{n}.json non esiste"); return 2
    if not os.path.exists(pp):
        print(f"part_{n}.json non esiste ancora"); return 2
    chunk = json.load(open(cp, encoding="utf-8"))
    try:
        part = json.load(open(pp, encoding="utf-8"))
    except Exception as e:
        print(f"part_{n}.json non e' JSON valido: {str(e)[:120]}"); return 2

    expected = {e["en"]: e for e in chunk}
    orphans = [k for k in part if k not in expected]
    empty = [k for k, v in part.items() if not str(v).strip()]
    missing = [e for e in expected if e not in part]

    print(f"slice {n}: {len(part)} consegnate su {len(chunk)} assegnate")
    result = 0
    if orphans:
        result = 1
        print(f"\nCHIAVI CHE NON COMBACIANO CON L'INGLESE RICEVUTO: {len(orphans)}")
        print("  (verranno perse alla fusione: la chiave dev'essere identica carattere per carattere)")
        for k in orphans[:10]:
            print(f"    {k[:110]!r}")
    if empty:
        result = 1
        print(f"\nTRADUZIONI VUOTE: {len(empty)}")
        for k in empty[:10]:
            print(f"    {k[:110]!r}")

    rules = load_rules()
    pairs = [(en, it) for en, it in part.items() if en in expected and str(it).strip()]
    certain, suspect = untranslated(pairs, rules[1])
    if certain:
        result = 1
    show_english(certain, suspect)

    prob = analyze(pairs, rules)
    if prob:
        result = 1
        tot = sum(len(v) for v in prob.values())
        print(f"\nSEGNALAZIONI SUL CONTENUTO: {tot}")
        show_report(prob, how_many=2)
    else:
        print("\ncontenuto: nessuna segnalazione")

    if missing:
        print(f"\nassegnate ma non consegnate: {len(missing)}")
        print("  (se sono note interne di sviluppo o identificatori, l'omissione e' corretta)")
        for e in missing[:15]:
            print(f"    ricorre {expected[e]['ricorre']:>3}  {expected[e]['dove']}\n       {e[:100]!r}")
    if result == 0 and not missing:
        print("\nfetta completa e pulita")
    return result


def dictionary():
    """Lo stesso controllo sul dizionario intero: serve a sapere se un giro
    precedente ha gia' lasciato passare qualcosa."""
    d = json.load(open(DICT, encoding="utf-8"))
    certain, suspect = untranslated(d["strings"].items(), load_rules()[1])
    known = intended()
    chosen = [(en, it) for en, it in certain if en in known]
    certain = [(en, it) for en, it in certain if en not in known]
    suspect = [(en, it) for en, it in suspect if en not in known]
    print(f"{len(d['strings'])} stringhe nel dizionario")
    if chosen:
        print(f"  {len(chosen)} restano in inglese per scelta verificata "
              f"(translations/identiche-volute.json)")
    show_english(certain, suspect, how_many=20)
    if not certain and not suspect:
        print("nessuna resa rimasta in inglese senza una ragione scritta")
    return 1 if certain else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dictionary":
        sys.exit(dictionary())
    sys.exit(main(int(sys.argv[1])))
