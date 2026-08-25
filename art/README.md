# Copertine dei libri

Le tre localizzazioni ufficiali di BOOK OF HOURS — russo, giapponese, cinese —
traducono i titoli dei libri **e ridisegnano le copertine**: il gioco spedisce
quattro set d'arte completi, uno per cultura, dentro `resources.assets`. Il
russo mette iniziali cirilliche, giapponese e cinese un titolo breve in
caratteri CJK. Nessuna delle tre affianca l'inglese al titolo tradotto.

Per i locmod il kit ufficiale è esplicito: «Sorry, you will need to provide your
own images, if the original ones don't suit your purposes!», con il permesso di
partire dalle immagini originali.

## Cosa c'è qui

```
plates/     483 PNG: le copertine con la scritta inglese cancellata. Sono il
             nostro lavoro, e sono versionate.
font/        EB Garamond (SIL OFL), lo stesso serif del gioco. Ridistribuibile.
manifest.json  per ogni libro: titolo inglese, titolo italiano, sigla proposta.

originals/  582 PNG: le copertine e i dorsi inglesi come li pubblica Weather
             Factory. NON MODIFICARE: servono da riferimento.
extracted/   i quattro set di sprite del gioco (en, ru, jp, zh-hans), da cui
             plates.py ricava le lastre.
```

**Le ultime due non stanno in git**: sono arte di Weather Factory, e il
repository non la ridistribuisce. Si rimettono in casa da fonti legittime, e lo
fa `tools/sources.py`:

```sh
python3 tools/sources.py             che cosa c'è e che cosa manca
python3 tools/sources.py originals   scarica lo ZIP pubblicato da Weather Factory
python3 tools/sources.py extracted    estrae gli sprite dal gioco installato
```

Lo ZIP degli originali è `https://weatherfactory.biz/wp-content/uploads/2025/04/book_covers.zip`,
che Weather Factory pubblica per i modder; le estratte escono da
`resources.assets` della propria copia del gioco, con `plates.py extract`.
Il font viene da `https://github.com/octaviopardo/EBGaramond12`.

## Il lavoro, diviso in due

**A mano**: cancellare la scritta inglese dai file in `plates/`, in place.
Nient'altro. Non spostare, non ritagliare, non riscalare, non rinominare: il
file deve restare delle stesse dimensioni dell'originale.

Non serve annotare dove stava la scritta né di che colore era. `covers.py` li
ricava confrontando la lastra con l'originale: dove i due file differiscono
c'era il testo, e il colore è quello dei pixel dell'originale in quel punto. È
anche il motivo per cui `originals/` non va toccata.

**A macchina**: `python3 tools/covers.py` scrive la sigla italiana su ogni
lastra ripulita e salva il risultato in
`mod/BookOfHours_italian/images/books/loc_it/`, e in nessun altro posto: la
copia che teneva anche in `art/italiano/` era identica bit per bit, e git se la
portava dietro due volte.

## Dove il gioco cerca davvero le copertine

`images/books/loc_it/t.<id>.png` per la copertina, `t.<id>_.png` per il dorso.
Non `images/books/`, che era quello che `covers.py` usava, e non
`images/localised/`, che è dove il mod spagnolo mette le sue due immagini.

Non è dedotto per analogia: sta nel codice del gioco, in
`bh_Data/Managed/SecretHistories.Main.dll`.

```
ResourcesManager.GetSpriteForBookCover(icon):
    TryGetSpriteLocalised("books", icon, Config.GetConfigValue("Culture"))
    se torna null -> GetSprite("books", icon)          # la copertina inglese

ResourcesManager.TryGetSpriteLocalised(cartella, file, cultura):
    se cultura != "en":
        loc = "loc_[culture]".Replace("[culture]", cultura)     # -> loc_it
        Path.Combine("images", cartella, loc, file)             # images/books/loc_it/t.xxx
```

La chiave con cui un mod registra un'immagine è il suo **percorso relativo alla
radice del mod, senza estensione**: `ModManager.LoadImage` toglie dal percorso
la radice del mod e l'estensione, e `ModManager.GetSprite` cerca esattamente
quella stringa. Per questo il file deve stare in
`BookOfHours_italian/images/books/loc_it/t.xxx.png` e non altrove.

Scriverle dritte in `images/books/` funzionerebbe lo stesso — è il ramo di
ripiego, che pesca nei mod prima che nelle risorse del gioco — ma sostituirebbe
la copertina **per tutte le culture**: chi tiene il gioco in inglese col mod
installato vedrebbe le sigle italiane. La sottocartella per cultura esiste per
evitare proprio questo.

`images/localised/` è un'altra cosa ancora: `BabelfishImage.DisplayImageForCulture`
la usa per le immagini che portano testo dentro l'illustrazione — le insegne del
villaggio, le etichette della mappa — e non per le copertine dei libri.

Resta da confermare **in partita**, aprendo uno scaffale della biblioteca: i
file ci sono comunque, quindi nessun controllo del repository si accorgerebbe di
un percorso sbagliato.

```sh
python3 tools/covers.py --list          # a che punto siamo
python3 tools/covers.py                  # tutte le lastre pronte
python3 tools/covers.py t.blacknephrite  # una sola
```

Lo script si può rilanciare quante volte si vuole: rilegge le lastre e riscrive
l'uscita. Se una sigla non convince, si cambia in `manifest.json` (campo
`sigla`) e si rilancia. Il campo `peso` accetta `regular`, `medium`, `semibold`,
`bold` per scegliere il taglio del Garamond.

## Le sigle

Seguono lo schema degli originali inglesi: iniziale maiuscola per le parole
piene, minuscola per le funzionali, articolo iniziale omesso.

| inglese | | italiano | |
|---|---|---|---|
| Gospel of Nicodemus | `GoN` | Vangelo di Nicodemo | `VdN` |
| A Catalogue of Uncharted Pleasures | `aCoUP` | Un Catalogo di Piaceri Inesplorati | `uCdPI` |
| Black Nephrite | `BN` | Nefrite Nera | `NN` |
| Exorcism for Girls | `EfG` | Esorcismo per Ragazze | `EpR` |

Sulla copertina la sigla sta su una riga; sul dorso, che è stretto, le lettere
si impilano **dritte** (`G` / `o` / `N`) o si spezzano in due righe (`aCo` /
`UP`). Non vanno mai ruotate: negli originali sono sempre in piedi.

## Cosa non va rifatto

- **27 copertine puramente pittoriche**, senza lettere: *A Novel Method for
  Invocation & Contrition* (un serpente), *The Book of the White Cat* (un
  gatto), i tre *Geminiad*, *The Berrybook*… Nemmeno le tre ufficiali le hanno
  toccate. Le ultime due sono state riconosciute tardi, perché il manifest le
  dava con testo: si vedono a occhio, e nelle quattro culture sono identiche.
- **10 titoli che restano invariati** perché latini, in lingua inventata o nomi
  propri: *Codex Acephali*, *De Bellis Murorum*, *Enchiridion Tragularis*, *Nix
  Abolix*, *OGHKOR OGHKOR TISSILAK OGHKOR*… la sigla inglese continua a valere,
  ed è la ragione per cui `covers.py --list` non li conta più come lavoro
  arretrato: li elenca a parte, come decisi.

Erano dati per invariati anche *COLOURS IN THE LIVER*, *EXPERIMENT BEYOND SIGHT*
e *THE OPEN HEAD*, ma il dizionario li traduce (*COLORI NEL FEGATO*,
*ESPERIMENTO OLTRE LA VISTA*, *LA TESTA APERTA*): le loro copertine sono state
rifatte, e ora mostrano `CnF`, `EOlV`, `LTA`.

Tre libri — *The Iron Book*, *The Ivory Book*, *The Silver Book* — sembravano
senza testo e non lo erano: il loro sprite inglese è **quattro pixel più alto**
di quello delle altre culture, e `plates.py` saltava il confronto quando le
dimensioni non coincidevano. Ora allinea cercando lo scarto che minimizza la
differenza, e quelle tre copertine hanno la sigla italiana (`ILdF`, `ILdA`…).

In tutto: **244 copertine e 237 dorsi** scritti, e `covers.py --list` dice
«niente da rifare».
