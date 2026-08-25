"""Avanzamento: quanto testo del gioco e' tradotto, e fra quanto finisce.

Due domande diverse, che qui stanno insieme.

 Attenzione a non confonderlo con coverage.py: qui si contano le *voci del
 dizionario* (translations/it.json), la' i *campi dei file del mod*. Una stringa
 senza voce nel dizionario risulta mancante qui, ma presente la', perche'
 apply.py in quel caso lascia l'inglese e il campo nel file c'e'. I due numeri
 divergono ed e' giusto cosi'; tools/identical.py e' il terzo, e dice quali
 delle rese presenti sono ferme sull'inglese.

 - Quanto manca al gioco. Non si misura in stringhe distinte ma in *campi*: la
   stessa frase inglese ricorre in piu' entita' ("Memory" 669 volte), e tradurla
   una volta ne copre 669. E si misura soprattutto in parole, perche' una label
   di due parole e una descrizione di sessanta non sono lo stesso lavoro.
   Conta anche il lavoro consegnato e non ancora fuso: i part_N.json in corso.

 - Fra quanto finisce. Il ritmo non si puo' dedurre da una fotografia, quindi a
   ogni lettura se ne salva una riga in .andamento.jsonl e la velocita' si
   misura sulla finestra osservata. Le prime letture non sanno ancora dire nulla;
   dopo due o tre l'ETA si stabilizza.

Uso: python progress.py [--follow [secondi]] [--recompute]
"""
import json, glob, os, re, sys, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bohloc import PROJ
from split import SKIP

PARTS = os.path.join(PROJ, "translations", "parts")
DICT = os.path.join(PROJ, "translations", "it.json")
CACHE = os.path.join(PROJ, "translations", ".corpus.json")
LOG = os.path.join(PARTS, ".andamento.jsonl")


def corpus(recompute=False):
    """{inglese: [campi in cui ricorre, parole]} + totali. In cache: leggerlo costa 6s."""
    if not recompute and os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    from bohloc import load_tree, CORE
    core, *_ = load_tree(CORE)
    st = {}
    for v in core.values():
        for txt in v["strings"].values():
            t = txt.strip()
            if not t:
                continue
            if t not in st:
                st[t] = [0, len(t.split())]
            st[t][0] += 1
    data = {"stringhe": st,
            "campi_tot": sum(v[0] for v in st.values()),
            "parole_tot": sum(v[0] * v[1] for v in st.values())}
    json.dump(data, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return data


def num(p):
    return re.search(r"(\d+)", os.path.basename(p)).group(1)


def read_lines(p):
    """Tollerante: un file in corso di scrittura non deve far fallire il monitor."""
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        try:
            text = open(p, encoding="utf-8").read()
            return {} if not text.strip() else \
                   dict.fromkeys(re.findall(r'^\s*"(.*?)"\s*:', text, re.M))
        except Exception:
            return {}


def duration(sec):
    sec = int(max(0, sec))
    if sec < 90:
        return f"{sec}s"
    if sec < 5400:
        return f"{sec // 60}m"
    return f"{sec // 3600}h{(sec % 3600) // 60:02d}m"


def bar(pct, n=20):
    full_items = int(round(pct / 100 * n))
    return "#" * full_items + "." * (n - full_items)


def history():
    if not os.path.exists(LOG):
        return []
    outside = []
    for line in open(LOG, encoding="utf-8"):
        try:
            outside.append(json.loads(line))
        except Exception:
            pass
    return outside


# Un ritmo si misura solo su un movimento vero. Una slice chiusa che riceve una
# correzione di una stringa non e' un traduttore al lavoro: presa per tale dava
# 0,1 stringhe/minuto e un ETA di 2.683 ore.
MIN_MOVEMENT = 10          # stringhe
MIN_WINDOW = 180          # secondi


def rate(samples, n, current, now):
    """stringhe al minuto per la slice n, misurate sulla finestra osservata."""
    series = [(c["t"], c.get("slice", {}).get(str(n))) for c in samples
             if c.get("slice", {}).get(str(n)) is not None and c.get("slice", {})[str(n)] < current]
    # Da dove far partire la finestra. Non dalla prima lettura in assoluto: quella
    # comprende l'avvio dell'agente, e in un caso ha compreso venti minuti di un
    # agente nato morto, facendo scendere il ritmo a 1,1 stringhe/minuto.
    # Se c'e' gia' una lettura con del lavoro fatto, si misura da li' -- e' regime.
    # Altrimenti si prende l'ULTIMA lettura a zero, che e' la stima piu' stretta
    # del momento in cui il lavoro e' cominciato.
    processed = [x for x in series if x[1] > 0]
    start_from = processed[0] if processed else (series[-1] if series else None)
    if not start_from:
        return None
    moved, duration_s = current - start_from[1], now - start_from[0]
    if moved < MIN_MOVEMENT or duration_s < MIN_WINDOW:
        return None
    return moved / (duration_s / 60)


def one_reading(data, samples):
    now = time.time()
    chunks = sorted(glob.glob(os.path.join(PARTS, "chunk_*.json")),
                    key=lambda p: int(num(p)))
    st = data["stringhe"]
    d = json.load(open(DICT, encoding="utf-8"))["strings"]
    done_now, lines = {}, []
    tot_a = tot_f = 0
    rates, slice_end = [], []
    silent_ones = 0
    delivered = set()

    for c in chunks:
        n = int(num(c))
        assigned = len(read_lines(c))
        pp = os.path.join(PARTS, f"part_{n}.json")
        dd = os.path.join(PARTS, f"dubbi_{n}.json")
        # il lavoro in corso arriva a frammenti (join.py li ricompone alla fine):
        # il monitor deve vedere anche quelli, altrimenti la slice sembra ferma
        pieces = sorted(glob.glob(os.path.join(PARTS, f"part_{n}.[0-9]*.json")))
        part = read_lines(pp) if os.path.exists(pp) else {}
        for q in pieces:
            part.update(read_lines(q))
        touched_ids = [f for f in ([pp] if os.path.exists(pp) else []) + pieces]
        if touched_ids:
            done = len(part)
            delivered |= set(part)
            eta_file = now - max(os.path.getmtime(f) for f in touched_ids)
        else:
            done, eta_file = 0, None
        done_now[str(n)] = done
        doubts = len(read_lines(dd)) if os.path.exists(dd) else 0
        pct = 100 * done / assigned if assigned else 0

        # "attiva" si deduce dal movimento fra due letture o dai frammenti in corso,
        # non dalla data del file: riallineare i part_N.json li faceva sembrare vivi.
        last_one = next((c.get("slice", {}).get(str(n)) for c in reversed(samples)
                       if c.get("slice", {}).get(str(n)) is not None), None)
        active = done < assigned and (bool(pieces) or (last_one is not None and done > last_one))
        r = rate(samples, n, done, now) if active else None
        if r and r > 0:
            rates.append(r)
            slice_end.append((assigned - done) / r * 60)
            tail = f"{r:4.1f} str/min  finisce fra {duration((assigned - done) / r * 60)}"
        elif done >= assigned and assigned:
            tail = "consegnata"
        elif active:
            silent_ones += 1
            tail = f"in corso da {duration(eta_file)}, ritmo non ancora misurabile"
        elif done == 0:
            tail = "non ancora iniziata"
        else:
            tail = f"ferma, mancano {assigned - done}"
        lines.append(f"  slice {n:>2}  [{bar(pct)}] {done:>4}/{assigned:<4} {pct:5.1f}%  "
                     f"dubbi {doubts:<3} {tail}")
        tot_a += assigned
        tot_f += done

    # quanto testo del gioco e' coperto, contando anche il non ancora fuso
    translated = set(d) | {k for k in delivered if k in st}
    fields = sum(st[k][0] for k in translated if k in st)
    words = sum(st[k][0] * st[k][1] for k in translated if k in st)
    # le note interne di sviluppo non si tradurranno mai: il 100% e' li', non a 17.926
    excluded = [k for k in st if SKIP.search(k) or len(k.strip()) <= 1]
    skipped_fields = sum(st[k][0] for k in excluded)
    skipped_words = sum(st[k][0] * st[k][1] for k in excluded)
    total_fields = data["campi_tot"] - skipped_fields
    total_words = data["parole_tot"] - skipped_words
    remaining_str = len([k for k in st if k not in translated and k not in set(excluded)])

    out = lines + ["", f"  totale consegnato in questo giro: {tot_f}/{tot_a}"
                       f" ({100 * tot_f / tot_a if tot_a else 0:.1f}%)", "",
                   "  TESTO DEL GIOCO", "",
                   f"    campi     {fields:>7} / {total_fields:<7} {100 * fields / total_fields:5.1f}%"
                   f"   [{bar(100 * fields / total_fields)}]",
                   f"    parole    {words:>7} / {total_words:<7} {100 * words / total_words:5.1f}%"
                   f"   [{bar(100 * words / total_words)}]",
                   f"    (escluse {len(excluded)} stringhe di servizio, {skipped_words} parole,"
                   f" che restano in inglese apposta)", ""]

    tot_ritmo = sum(rates)
    out.append("  ANDAMENTO")
    out.append("")
    if not rates:
        out.append("    ritmo non ancora misurabile: servono due letture a distanza, con almeno")
        out.append(f"    {MIN_MOVEMENT} stringhe di movimento in mezzo")
        if silent_ones:
            out.append(f"    ({silent_ones} slice hanno un traduttore al lavoro che non ha ancora consegnato)")
        out.append(f"    restano {remaining_str} stringhe distinte, {total_words - words} parole")
        out.append("    (sono stringhe senza voce nel dizionario: apply.py le lascia in inglese,")
        out.append("     quindi coverage.py non le vede come mancanti. tools/identical.py dice")
        out.append("     per ciascuna se e' una scelta verificata o un buco)")
        return "\n".join(out), {"t": now, "slice": done_now}

    per_agent = sorted(rates)[len(rates) // 2]
    out.append(f"    ritmo      {per_agent:.1f} stringhe/min per agente, {tot_ritmo:.1f} in tutto"
               f"  ({len(rates)} misurati" + (f", {silent_ones} non ancora misurabili)" if silent_ones else ")"))

    if slice_end:
        tail = f"    questo giro finisce fra {duration(max(slice_end))}"
        if silent_ones:
            tail += f"  (piu' le {silent_ones} slice che non hanno ancora consegnato)"
        out.append(tail)

    # il progetto non si stima sul ritmo istantaneo ma a giri: le slice non ancora
    # assegnate non hanno un agente, e il parallelismo lo si sceglie, non lo si misura.
    per_round = len(rates) + silent_ones or 1
    large = max((len(read_lines(c)) for c in chunks), default=400)
    rounds = -(-remaining_str // (per_round * large))
    hours_per_round = large / per_agent / 60
    sec = rounds * hours_per_round * 3600
    end = time.localtime(now + sec)
    out.append("")
    out.append(f"    un giro da {per_round} agenti x {large} stringhe dura ~{duration(hours_per_round * 3600)}")
    out.append(f"    restano {remaining_str} stringhe: {rounds} giri cosi', ~{duration(sec)} di lavoro")
    out.append(f"    (fine {time.strftime('%d/%m alle %H.%M', end)} se si tiene questo passo"
               f" senza pause; a 5 agenti per giro sarebbe"
               f" ~{duration(-(-remaining_str // (5 * large)) * large / per_agent * 60)})")
    return "\n".join(out), {"t": now, "slice": done_now}


def main():
    a = sys.argv[1:]
    data = corpus("--recompute" in a)
    follow = "--follow" in a
    each = 60
    if follow:
        i = a.index("--follow")
        if i + 1 < len(a) and a[i + 1].isdigit():
            each = int(a[i + 1])
    while True:
        samples = history()
        text, sample = one_reading(data, samples)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample) + "\n")
        if follow:
            print("\033[2J\033[H", end="")
            print(time.strftime("  %H.%M.%S"), "\n")
        print(text)
        if not follow:
            return
        time.sleep(each)


if __name__ == "__main__":
    main()
