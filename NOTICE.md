# Di chi è che cosa

Questo repository mette insieme quattro cose con quattro proprietari diversi.
Vale la pena tenerle distinte.

## Il codice: mio, MIT

Gli strumenti in `tools/`, i test in `tests/` e la documentazione sono miei e
stanno sotto licenza MIT. Il testo della licenza è in [`LICENSE`](LICENSE).

## Il testo del gioco: di Weather Factory

L'inglese originale di BOOK OF HOURS e del DLC HOUSE OF LIGHT è di Weather
Factory Ltd. Qui compare due volte, e in entrambi i casi perché serve a
tradurre: come chiave del dizionario in `translations/it.json`, e come
riferimento in `mod/BookOfHours_italian/loc/`. Non è ridistribuito per altro.

## La traduzione italiana: mia, ed è della comunità

La resa italiana è mia, ed è pubblicata come traduzione della comunità
attraverso il sistema di locmod ufficiale di Weather Factory.

**Ufficiale è il sistema, non questa traduzione.** Weather Factory non l'ha
commissionata, rivista né approvata. Sul Workshop il mod porta il tag
`Community Translation`.

## L'arte: di Weather Factory, in due forme diverse

Le copertine dei libri in `mod/BookOfHours_italian/images/` sono le loro
illustrazioni con le sigle italiane reimpresse sui dorsi. Sono lavoro derivato
dalla loro arte, e stanno qui perché **sono il mod**: distribuire asset
localizzati è esattamente ciò a cui serve il sistema di locmod.

Le **lastre** intermedie, cioè le stesse illustrazioni con la scritta inglese
cancellata, non stanno in questo repository e non ci devono stare. Una lastra è
arte di Weather Factory in una forma più riutilizzabile della copertina finita:
è una tela pulita. Chi lavora al progetto se le rigenera in locale con
`python3 tools/plates.py build`, che le ricava da un gioco installato mettendo a
confronto le quattro localizzazioni ufficiali.

Con un'eccezione misurata: **quattordici lastre non si rigenerano**, perché nel
2026 sono state ritoccate a mano dove la cancellatura automatica lasciava
inchiostro o mangiava un pezzo di disegno. Quali sono, e quanto se ne discosta
il risultato automatico, sta in [`art/LASTRE-A-MANO.md`](art/LASTRE-A-MANO.md) —
che è un elenco di nomi, non arte, e per questo sta in git.

## Il font: EB Garamond, OFL

`art/font/` contiene EB Garamond sotto SIL Open Font License 1.1. La licenza sta
accanto ai file, in [`art/font/OFL.txt`](art/font/OFL.txt).

---

BOOK OF HOURS e HOUSE OF LIGHT sono marchi di Weather Factory Ltd. Questo
progetto non è affiliato a Weather Factory.
