# Traduzione italiana di BOOK OF HOURS

Localisation mod (locmod) per BOOK OF HOURS e il DLC HOUSE OF LIGHT, secondo il
sistema ufficiale di Weather Factory. Il sistema è ufficiale; la traduzione no,
è una traduzione della comunità.

**È fatta con l'IA.** Il testo l'ha prodotto Claude, e l'hanno riletto ChatGPT e
di nuovo Claude. Le convenzioni di traduzione, le decisioni sui casi dubbi e gli
undici controlli automatici sono lavoro umano. La scheda del mod lo dichiara.

## Stato

L'interfaccia è tradotta e completa (295/295 label). **Anche i contenuti lo
sono**: 99,8 % dei campi e 100 % delle parole, da 12.646 stringhe distinte.
Le copertine dei libri sono rifatte con le sigle italiane: 244 copertine e 237
dorsi, e `covers.py --list` dice «niente da rifare».

Quello che resta identico all'inglese ci resta apposta, ed è verificato voce per
voce: 57 testi con la ragione scritta accanto in
`translations/identiche-volute.json`, più i nomi propri e il lessico inventato
(`Ereb`, `Fet`, `Chor`). `tools/identical.py` rifà il conto e non trova buchi.

Da fare: **rivedere il testo a schermo giocando**. È la ragione per cui la
versione è ancora una 0.x e non una 1.0.

### Tre conteggi che rispondono a tre domande diverse

Leggendoli di fila sembrano contraddirsi, e non lo sono:

| strumento | conta | dice |
|---|---|---|
| `coverage.py` | i campi dei file del mod | esiste una riga italiana per ogni campo del gioco? |
| `progress.py` | le voci di `translations/it.json` | quanto lavoro di traduzione resta? |
| `identical.py` | le rese uguali all'inglese | quali di quelle righe sono ferme sull'inglese, e perché? |

Le 97 stringhe che `progress.py` chiama mancanti non hanno voce nel dizionario:
`apply.py` in quel caso lascia l'inglese, quindi il campo nel file c'è e
`coverage.py` non le vede come mancanti. Tutte e 97 sono classificate da
`identical.py` come scelte verificate.

## Struttura

```
CLAUDE.md                     come si tocca il repository senza romperlo
requirements.txt              le quattro dipendenze Python
percorsi.esempio.json         dove sta il gioco: da copiare in percorsi.json
docs/
  analisi-stato.md            confronto con i mod spagnolo e francese, con i numeri
  convenzioni.md              decisioni di traduzione da applicare uniformemente
  glossario-non-tradurre.json termini che FR ed ES lasciano entrambi in inglese
translations/
  it.json                     il dizionario: inglese -> italiano
  glossario.json              i termini vincolanti, quelli che validate.py fa rispettare
  mod.json                    i metadati del mod: nome, autore, versione, descrizioni
  identiche-volute.json       le rese uguali all'inglese per scelta, con la ragione
  parts/                      le slice in lavorazione
art/                          il laboratorio delle copertine
  lastre/                     le copertine con la scritta inglese cancellata
  font/                       EB Garamond (SIL OFL), il serif del gioco
  manifest.json               titolo inglese, titolo italiano e sigla, per libro
  originali/ estratte/        arte di Weather Factory: fuori da git, le rimette
                              in casa tools/sources.py
mod/BookOfHours_italian/      albero di lavoro del mod
  content/cultures/culture.json   la cultura 'it' e le 295 UI labels
  loc/loc_it/                     i contenuti tradotti
  images/books/loc_it/            le copertine e i dorsi con le sigle italiane
  cover.png                       l'immagine della scheda, generata da tools/cover.py
  loc/_origignal_from_core/       copia dell'originale inglese, per riferimento
  loc/_mod_in_french/             il mod francese, per riferimento
dist/                         il pacchetto costruito da pack.py (fuori da git)
tools/                        script di analisi (richiedono json5)
```

## Requisiti

**Serve BOOK OF HOURS installato**, e non per comodità. `bohloc.py` punta dentro
`bhcontent/core`, cioè dentro il gioco, e da lì leggono quasi tutti gli
strumenti:

- `apply.py` percorre i file del gioco per sapere quali campi tradurre, quindi
  **senza il gioco il mod non si rigenera dal dizionario** — e `pack.py` comincia
  proprio da `apply.py`, quindi non si costruisce nemmeno il pacchetto;
- `validate.py` e `glyphcheck.py` ci cercano `_core.txt`, l'atlante dei glifi del
  font, per sapere quali caratteri il gioco sa disegnare;
- `plates.py` tira le quattro localizzazioni ufficiali fuori da
  `resources.assets` per ricostruire `art/lastre/`, che in git non c'è (vedi
  [`NOTICE.md`](NOTICE.md)), e senza le lastre `covers.py` non rifà le copertine.

Per **usare** la traduzione niente di tutto questo serve: si scarica dal
Workshop e basta. I requisiti qui sotto riguardano chi ci lavora.

Poi tre cose, e una che le verifica tutte.

**1. Il venv e le dipendenze.** Quattro pacchetti: `json5` legge i JSON del
gioco (virgole finali, a volte UTF-16), `Pillow` e `numpy` rifanno copertine e
insegne, `UnityPy` tira gli sprite fuori da `resources.assets`.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
source .venv/bin/activate     # poi «python3 tools/...» come nel resto del README
```

**2. Un font lineare di sistema**, per la targa dell'ufficio postale in
`signs.py`. Il Garamond dei libri sta nel repository, questo no:

```sh
sudo dnf install urw-base35-fonts     # Fedora
sudo apt install fonts-urw-base35     # Debian, Ubuntu
```

Vanno bene anche FreeSans Bold o Liberation Sans Bold: `bohloc.py` prova i tre
in fila, e con la chiave `font_insegna` in `percorsi.json` se ne indica un altro.

**3. Il materiale che non ridistribuiamo.** `art/originali/`, `art/estratte/` e
`art/lastre/` sono arte di Weather Factory e stanno fuori da git. Si rimettono in
casa in tre comandi, tutti su un gioco installato:

```sh
python3 tools/sources.py originals   # lo ZIP che WF pubblica per i modder
python3 tools/sources.py extracted    # gli sprite del gioco, via UnityPy
python3 tools/plates.py extract       # le quattro localizzazioni ufficiali
python3 tools/plates.py build          # e da quelle, art/lastre/
```

`plates.py build` non chiede niente a mano: ricava dove sta il testo confrontando
inglese e russo, e per ogni pixel dentro quel riquadro sceglie fra le quattro
lingue quella che lì ha il pannello pulito. Ci vuole qualche minuto. I percorsi
del gioco stanno in `percorsi.json` (si copia `percorsi.esempio.json`).

**La verifica.** Dice che cosa manca e come si rimedia, riga per riga:

```sh
python3 tools/prereqs.py           la lista
python3 tools/prereqs.py --verify   e la mette alla prova per davvero
```

`--verify` non si fida della lista: fa girare `apply.py --dry`, rigenera una
copertina in una cartella temporanea e la confronta con quella spedita, legge un
file del gioco e apre il font delle insegne. Esce con 1 se qualcosa non regge,
così si può mettere in testa a un altro script.

## Installazione

Due cose diverse, che prima erano lo stesso comando: provare le proprie
modifiche e installare il mod. Il `cp -r` dell'albero di lavoro faceva
entrambe, ed è il motivo per cui il pacchetto si portava dietro 13 MB di
materiale di riferimento.

### Per chi lavora al repository

```sh
python3 tools/pack.py --no-zip --install
```

Rigenera i file dal dizionario, passa i cancelli — e **si ferma se uno non è
pulito** — costruisce `dist/BookOfHours_italian/` con solo ciò che il gioco
legge, e lo copia nella cartella `mods` del gioco. Il
`serapeum_catalogue_number.txt`, che il gioco scrive al primo caricamento sul
Workshop, viene conservato fra un'installazione e l'altra.

Poi, nel gioco: Opzioni → Mods per abilitarlo, Opzioni → Lingua per scegliere
l'italiano. La cartella dei mod è in `tools/bohloc.py` (`MODS`); qui è quella di
Steam via Flatpak, altrimenti si trova da Opzioni → BROWSE FILES.

### Per chi lo scarica

Dallo **Steam Workshop**: iscriversi all'oggetto e riavviare il gioco. Il mod
compare in Opzioni → Mods e la lingua in Opzioni → Lingua.

Dallo **zip**: scompattare `BookOfHours_italian-<versione>.zip` dentro la
cartella `mods` del gioco, in modo che il percorso finale sia
`mods/BookOfHours_italian/synopsis.json`. La cartella `mods` si apre dal gioco
con Opzioni → BROWSE FILES.

## I test

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

335 test in un minuto, e non toccano niente: gli strumenti che scrivono - apply,
merge, split, covers - si provano puntandoli a cartelle temporanee, mai al
dizionario o al mod veri. Quelli che hanno bisogno del gioco installato si
saltano da soli su una macchina che non ce l'ha.

Sono divisi in due strati. Lo **smoke** passa su tutti e 39 gli script: ognuno
compila, dice a che cosa serve, si importa senza fare niente, e non documenta
flag che poi non legge. E' la rete che prende i guasti da rinomino, quelli che
un test mirato non vede perche' importa solo cio' che gia' funziona. Gli **unit
test** stanno sui casi in cui una versione precedente sbagliava: il genitivo
sassone contato come virgoletta aperta, il nome proprio scambiato per resa
mancante, «dall'XI secolo» segnalato come elisione sbagliata, i tre libri con lo
sprite quattro pixel piu' alto.

## I cancelli

Si rilanciano dopo ogni tornata, non alla fine. `tools/pack.py` li esegue tutti
e **si rifiuta di costruire il pacchetto** se uno non è pulito.

```sh
python3 tools/validate.py     glossario, neutro, markup, glifi
python3 tools/prose.py        ortotipografia della prosa
python3 tools/integrity.py    tag e a-capo nei file veri
python3 tools/glyphcheck.py   glifi contro l'atlante del font
python3 tools/identical.py    stringhe ferme sull'inglese: scelte contro buchi
python3 tools/grammar.py   accordi, elisioni, articoli
python3 tools/logic.py       numeri, negazioni e segni contro l'originale
python3 tools/checkpart.py --dictionary    rese rimaste in inglese
python3 tools/terms.py      label contro prosa (minuti)
python3 tools/consistency.py     un termine, una resa (minuti)
```

I quattro che hanno una zona grigia tengono un registro delle decisioni già
prese, così la lista resta chiusa invece di ripresentare ogni volta gli stessi
casi: `translations/identiche-volute.json`, `logica-verificate.json`,
`coerenza-verificate.json`, e il glossario per gli altri.

## Le partite già iniziate

Non tutto il testo sta nel compendio. Quando il gioco istanzia una postazione,
serializza nel salvataggio anche il suo `GoverningSphereSpec` — Label e
Description comprese — e al caricamento la ricrea da lì. In una partita
cominciata prima dell'installazione del mod, quelle stringhe restano com'erano.

È il caso che ha fatto perdere un pomeriggio: il bancone dell'Ufficio Postale
continuava a leggersi *Post Office Counter* in mezzo a una schermata italiana,
mentre il file loc era tradotto e installato. La prova sta nel salvataggio: su
1447 sfere serializzate, sei erano in inglese, ed erano esattamente le
postazioni del villaggio già visitate.

Una partita nuova non ha il problema. Per quelle in corso:

```sh
python3 tools/savegame.py            # dice che cosa cambierebbe
python3 tools/savegame.py --apply  # scrive, dopo una copia di sicurezza
```

Sostituisce solo dove il testo inglese è **esattamente** una chiave del
dizionario, e solo nei campi Label, Description, Desc, StartDescription.

## Pubblicazione

`python3 tools/pack.py` costruisce `dist/` e lo zip. La versione sta in un posto
solo, `translations/mod.json`, e da lì finisce in `synopsis.json`: se lo zip di
quella versione esiste già, `pack.py` si ferma invece di pubblicare due
contenuti diversi con lo stesso numero.

Il numero segue la forma del gioco, che si versiona a quattro componenti — il
suo `version.txt` dice `2026.5.g.1` — e `pack.py` rifiuta di costruire un
pacchetto con un numero scritto in un altro modo. La forma va fissata prima
della prima pubblicazione: cambiarla dopo lascia in giro pacchetti numerati in
due modi diversi, e non si sa più quale venga prima.

Sullo Steam Workshop si carica **dal gioco**: Opzioni → Mods, il pulsante di
caricamento accanto alla lingua. Il gioco pretende `cover.png` nella radice del
mod (`tools/cover.py` la genera) e scrive lui
`serapeum_catalogue_number.txt` con l'id dell'oggetto creato: quel file non va
composto a mano, o il caricamento successivo tenterebbe di aggiornare l'oggetto
di qualcun altro.

## Strumenti

Richiedono `json5`. I percorsi del gioco stanno in `percorsi.json`, che git non
segue: si copia `percorsi.esempio.json` e si correggono, oppure si passano
dall'ambiente (`BOH_GAME`, `BOH_MODS`, `BOH_LOC_ES`, `BOH_KIT`). Senza dire
niente, `bohloc.py` cerca il gioco nei posti soliti — Flatpak e Steam nativo — e
prende il primo che esiste.

### La catena della traduzione

| script | scopo |
|---|---|
| `extract.py` | cosa manca, per file, in ordine di lavoro |
| `split.py` | divide il da fare in slice, una per agente |
| `context.py` | per ogni slice, il campione di registro e il glossario che le servono |
| `join.py` | ricompone una slice dai salvataggi incrementali |
| `checkpart.py` | controlla una slice prima che rientri: il cancello di chi traduce, incluse le rese rimaste in inglese |
| `merge.py` | fonde le slice nel dizionario, intercettando orfane e collisioni |
| `titles.py` | riporta i titoli dei libri alla sola forma italiana (ha sostituito `booktitles.py`) |
| `validate.py` | controlla il dizionario: glossario, nomi propri, neutro, markup, glifi |
| `apply.py` | rigenera i file del mod dal dizionario, potando i campi di logica |
| `progress.py` | percentuale di testo tradotto, ritmo degli agenti, ETA |
| `pack.py` | costruisce il pacchetto da pubblicare, e con `--install` lo mette nel gioco |
| `savegame.py` | traduce i testi che il gioco ha già scritto dentro una partita salvata |

### Le copertine

I titoli sono in italiano puro, quindi le iniziali disegnate sulle copertine non
corrispondono più. Queste le rifanno.

| script | scopo |
|---|---|
| `sources.py` | riscarica il materiale di partenza che il repository non ridistribuisce |
| `plates.py` | ricava le copertine ripulite dalla scritta inglese |
| `initials.py` | ricalcola titoli italiani e sigle nel manifest |
| `covers.py` | scrive le sigle italiane sulle copertine ripulite |
| `index.py` | pagine di revisione: l'indice completo e le sole da controllare |
| `compare.py` | affianca ogni copertina originale alla lastra ripulita |
| `cover.py` | l'immagine della scheda del mod: uno scaffale di dorsi italiani |
| `signs.py` | rifà in italiano le scritte dipinte dentro le immagini: etichette della mappa, insegne |

### La revisione da fuori

| script | scopo |
|---|---|
| `review.py` | costruisce `dist/review-<versione>.zip`: solo testo, per farlo rileggere a un altro modello |

Dentro ci vanno il dizionario in slice da 500 voci con spagnolo e francese a
fronte, le label dell'interfaccia, le convenzioni e il glossario. Non ci vanno
codice, immagini, file del gioco né percorsi di questo computer.

### Analisi

| script | scopo |
|---|---|
| `prereqs.py` | la lista di cio' che serve per rigenerare, e `--verify` che la verifica |
| `bohloc.py` | lettore JSON tollerante (UTF-16, virgole finali, caratteri di controllo) |
| `coverage.py` | copertura IT/ES/FR rispetto all'originale inglese |
| `integrity.py` | tag, token, template e a-capo nei contenuti |
| `uicheck.py` | tag, chiavi mancanti e lunghezze nelle UI labels |
| `glyphcheck.py` | glifi usati contro l'atlante del font |
| `style.py` / `style2.py` / `style3.py` | ortotipografia delle UI label (con ES come metro), maiuscole (label lunghe / a due parole) |
| `prose.py` | ortotipografia della prosa: lineette, doppi spazi, virgolette annidate (`--apply` riscrive) |
| `terms.py` | dove la prosa nomina una carta senza usarne la label italiana |
| `identical.py` | le rese ferme sull'inglese, divise fra scelte verificate e buchi |
| `grammar.py` | accordi, elisioni, articoli, refusi di forma |
| `logic.py` | numeri, negazioni, domande e segni, confrontati con l'originale |
| `consistency.py` | un termine inglese reso in due modi diversi (ci mette minuti) |
| `sample.py` | campione affiancato CORE / IT / ES per ispezione visiva |
| `donottranslate.py`, `refine.py` | termini lasciati in inglese da FR ed ES |

## Diritti

Il codice di `tools/` è MIT ([`LICENSE`](LICENSE)). Il testo e l'arte del gioco
sono di Weather Factory; la traduzione italiana è mia, ed è una traduzione della
comunità fatta col loro sistema di locmod. Chi è proprietario di che cosa, e
perché le lastre non stanno in git, è spiegato in [`NOTICE.md`](NOTICE.md).

## Riferimenti

- [Locmod creation reference](https://weatherfactory.biz/book-of-hours-locmod-creation-reference/) — Weather Factory
- Il kit di localizzazione completo, che Weather Factory manda a chi lo chiede
- Mod spagnolo: Steam Workshop `1028310/3784793429` (Mrdynamite)
- Mod francese: [BoH_HoL-Fr su Nexus](https://www.nexusmods.com/bookofhours/mods/42)
