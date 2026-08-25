# Le plates ritoccate a mano

Il 2026-08-20 trentuno plates sono state ritoccate in un editor d'immagini,
dove la cancellatura automatica lasciava inchiostro residuo o mangiava un
pezzo di disegno. `plates.py` non sa rifare quel ritocco.

Da allora l'algoritmo e' migliorato, e ha recuperato buona parte di quel
lavoro da solo. Confrontando le plates spedite con quelle che `plates.py
build` produce oggi:

- **14 non si riproducono.** Sono l'unica cosa in questo progetto
  che nessuno script sa rifare. Stanno in `art/lastre-ritoccate-a-mano.zip`,
  che git non segue, e in `art/lastre.zip` insieme a tutte le altre.
- 17 oggi `plates.py` le rifa' identiche: il ritocco a mano e'
  diventato superfluo.

## Le non riproducibili

| plate | pixel che il build sbaglia |
|---|---|
| `t.apaleladyandaprinceofwines_` | 3356 |
| `t.calicitesupplications` | 2396 |
| `t.fekrisherbary` | 1816 |
| `t.fekrisherbary_` | 1765 |
| `t.aninvestigationofafounderedcountry_` | 1256 |
| `t.twowombsoneheart_` | 1132 |
| `t.atowerrises_` | 75 |
| `t.alightintheinkwell` | 54 |
| `t.anexorcistsfieldmanual_` | 36 |
| `t.acatalogueofunchartedpleasures_` | 9 |
| `t.anexorcistsfieldmanual` | 6 |
| `t.amanualfordeparture_` | 2 |
| `t.acatalogueofunchartedpleasures` | 1 |
| `t.amanualfordeparture` | 1 |

## Recuperate dall'algoritmo

- `t.anechoofsilence`
- `t.apaleladyandaprinceofwines`
- `t.ashapeinsmoke`
- `t.atowerfalls_`
- `t.bytheirmarksshallyeknowthem`
- `t.commandmentsforthepreservationofallthatexists`
- `t.cucurbitprisonerrecords1927_`
- `t.cucurbitprisonerrecords1928_`
- `t.deathsandtheirevasions`
- `t.exorcismforgirls`
- `t.gospelofnicodemus`
- `t.lakefucinorecordings_`
- `t.openingthesky`
- `t.operationsofacertainfinality`
- `t.theaccountofkanishkatthespidersdoor`
- `t.thelocksmithsdreamtrespasses`
- `t.themostsorrowfulendoftheladynonna_`

Il conto si rifa' cosi: si ricostruiscono le plates in una cartella
temporanea con `plates.py build` (dirottando `plates.PLATES`) e si
confrontano i pixel con quelle spedite.
