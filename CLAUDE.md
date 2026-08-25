# Come si lavora a questo repository

Traduzione italiana di BOOK OF HOURS e del DLC HOUSE OF LIGHT, come locmod
ufficiale di Weather Factory. Il `README.md` dice che cos'è e come si installa;
qui c'è come si tocca senza romperlo.

## Le tre regole che valgono sempre

1. **I file del mod non si scrivono a mano.** `mod/BookOfHours_italian/loc/loc_it/`
   e `content/cultures/culture.json` li rigenera `tools/apply.py` a partire da
   `translations/it.json`, che è il dizionario ed è l'unica fonte. Una correzione
   fatta sul file generato sparisce al primo `apply.py` che passa: va fatta nel
   dizionario.
2. **La versione sta in un posto solo**, `translations/mod.json`. Da lì
   `pack.py` scrive `synopsis.json`, nell'albero di lavoro e nel pacchetto. Se
   lo zip di quella versione esiste già, `pack.py` si ferma invece di pubblicare
   due contenuti diversi con lo stesso numero.
3. **Niente esce se un cancello non è pulito.** `pack.py` li esegue tutti e si
   rifiuta di costruire il pacchetto se uno segnala.

## I test

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

Girano in un minuto e non devono mai sporcare l'albero di lavoro: chi aggiunge
un test a uno strumento che scrive lo punta a `tmp_path`, non al dizionario.
Chi tocca uno strumento fa girare la suite prima di committare — lo smoke passa
su tutti e 39 gli script e prende i guasti da rinomino.

## I cancelli

Si rilanciano dopo ogni tornata, non alla fine.

```sh
python3 tools/validate.py     glossario, nomi propri, neutro, markup, glifi
python3 tools/prose.py        ortotipografia della prosa (--apply riscrive)
python3 tools/integrity.py    tag e a-capo nei file veri
python3 tools/glyphcheck.py   glifi contro l'atlante del font del gioco
python3 tools/identical.py    stringhe ferme sull'inglese: scelte contro buchi
python3 tools/grammar.py   accordi, elisioni, articoli
python3 tools/accords.py   articoli e preposizioni intorno ai nomi di gioco
python3 tools/logic.py       numeri, negazioni e segni contro l'originale
python3 tools/checkpart.py --dictionary    rese rimaste in inglese
python3 tools/terms.py      label contro prosa (minuti)
python3 tools/consistency.py     un termine, una resa (minuti)
```

Cinque hanno una zona grigia e tengono un registro delle decisioni già prese,
così la lista resta chiusa invece di ripresentare ogni volta gli stessi casi:
`translations/identiche-volute.json`, `logica-verificate.json`,
`coerenza-verificate.json`, `accordi-verificati.json`, e il glossario per gli altri. Una segnalazione si
chiude in due modi: correggendo il testo, oppure scrivendo lì la ragione per cui
resta com'è. Mai zittendo il controllo.

## Le convenzioni di traduzione

`docs/convenzioni.md` è vincolante, e `translations/glossario.json` è la parte
che `validate.py` fa rispettare a ogni passaggio. Le tre decisioni che si notano
subito:

- **Archivista**, non Bibliotecario: il gioco non dichiara mai il genere di chi
  lo gioca, e la prosa in prima persona cerca sempre una forma che non lo fissi —
  «Ho trovato la mia pace», non «Sono arrivato». Dove la forma neutra costava la
  frase — otto righe, tutte nei finali — si usa il maschile non marcato, e stanno
  scritte in `glossario.json` con la ragione (convenzioni 5-quaterdecies).
- **I quattordici Principi si traducono**: Lanterna, Forgia, Lama, Inverno,
  Cuore, Graal, Falena, Battente, Cielo, Luna, Nettare, Rosa, Squama, Suono.
- **I nomi propri restano in inglese**, sempre: Janus e non Giano, Lethe e non
  Lete. Vale anche per il lessico inventato — Ereb, Fet, Chor, Phost.

Quello che resta identico all'inglese ci resta apposta e va motivato voce per
voce in `translations/identiche-volute.json`: `identical.py` divide le scelte
verificate dai buchi, e i buchi devono restare zero.

## Le copertine dei libri

I titoli italiani cambiano le iniziali, quindi le sigle disegnate sui dorsi si
rifanno. La catena è `art/lastre/` (le copertine con la scritta inglese
cancellata) più `art/manifest.json` (titolo e sigla) → `tools/covers.py` →
`mod/BookOfHours_italian/images/books/loc_it/`, che è l'unico posto dove il
gioco le cerca. Per cambiare una sigla si tocca il manifest e si rilancia
`covers.py`, mai il PNG.

`art/originali/` e `art/estratte/` **non stanno in git**: sono arte di Weather
Factory, e le rimette in casa `tools/sources.py` — lo ZIP che pubblicano per i
modder, e l'estrazione dal gioco installato. Servono a `plates.py` e a
`covers.py`, quindi vanno recuperate prima di rifare le copertine.

## Prima di cominciare

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/prereqs.py --verify
```

`prereqs.py` elenca dipendenze, font, gioco installato e materiale d'arte,
dice come si rimedia a ciò che manca, e con `--verify` lo dimostra: rigenera una
copertina in una cartella temporanea e la confronta con quella spedita. Il
`README.md` ha la stessa lista per esteso.

## I percorsi del gioco

Dipendono da come è installato, non dal progetto: stanno in `percorsi.json`, che
git non segue. Si copia `percorsi.esempio.json` e si correggono, oppure si passa
tutto dall'ambiente (`BOH_GAME`, `BOH_MODS`, `BOH_LOC_ES`, `BOH_KIT`). Su
un'installazione ordinaria di Steam non serve scrivere niente: `tools/bohloc.py`
cerca nei posti soliti.

## Come è fatta la traduzione

Con modelli linguistici sotto guida umana, ed è dichiarato nella scheda del mod.
Le convenzioni sono decisioni prese e motivate a mano; il glossario le fa
rispettare a macchina; gli undici controlli qui sopra girano prima di ogni
pubblicazione. L'impalcatura degli agenti e i prompt di sessione restano fuori
da git: sono di chi lavora, non del mod. In git ci sta questo file, e
`AGENTS.md`, che è un collegamento a questo file: gli strumenti che cercano
quel nome trovano le stesse istruzioni, e non c'è una seconda copia da tenere
allineata.

## Come si scrive qui

Commenti e messaggi di commit in italiano. Il commit dice **perché**, non che
cosa: le alternative scartate e la ragione dello scarto valgono più dell'elenco
dei file toccati. Le decisioni di traduzione già prese si scrivono in
`docs/convenzioni.md`, così non si ridiscutono da capo.
