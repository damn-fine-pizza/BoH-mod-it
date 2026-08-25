# Di chi è che cosa

Questo repository mette insieme cose con proprietari diversi. Vale la pena
tenerle distinte, e dire per ognuna con quale permesso sta qui.

## Il permesso di Weather Factory

Non è una deduzione: è scritto nella loro pagina per chi fa un locmod.

> «Weather Factory grants permission for use and customisation of these images
> to create mods!»
>
> — [Book of Hours locmod creation reference](https://weatherfactory.biz/book-of-hours-locmod-creation-reference/)

Il permesso vale per tre categorie di immagini, che sono esattamente quelle che
questo mod tocca: le **immagini localizzate** (i cartelli dei luoghi, le insegne),
le **copertine e i dorsi dei libri**, e le **wallart**.

La cornice generale è la
[Sixth History Community Licence](https://weatherfactory.biz/sixth-history-community-licence/),
che consente di usare «fiction, characters, game mechanics and limited artwork»
di Cultist Simulator, BOOK OF HOURS e The Lady Afterwards, di ridistribuire, e
perfino di vendere sotto le 50.000 sterline l'anno. Vieta di rivendere un'opera
d'arte **da sola** (una stampa, un poster), di usare i logo ufficiali dei giochi,
e di copiare «all or a substantial part of our writing».

## Il codice: mio, MIT

Gli strumenti in `tools/`, i test in `tests/` e la documentazione sono miei e
stanno sotto licenza MIT. Il testo è in [`LICENSE`](LICENSE).

## L'arte: di Weather Factory, usata col loro permesso

`art/plates/` contiene le copertine dei libri con la scritta inglese cancellata.
Non le disegna nessuno: `tools/plates.py` le compone confrontando le quattro
localizzazioni ufficiali (inglese, russo, giapponese, cinese) e riempiendo la
zona del testo con pixel presi dal pannello stesso. Da lì `tools/covers.py`
reimprime la sigla italiana sul dorso, e il risultato è in
`mod/BookOfHours_italian/images/`, che è quello che il gioco carica.

Sono entrambe **customisation of these images to create mods**, cioè il caso
che il permesso qui sopra descrive alla lettera. Lo ZIP che Weather Factory
pubblica per i modder contiene le stesse copertine **con** la scritta inglese:
cancellarla e rimetterne un'altra è l'uso previsto, non un aggiramento.

Quattordici plates non si rigenerano, perché sono state ritoccate a mano dove la
cancellatura automatica lasciava inchiostro o mangiava un pezzo di disegno.
Quali sono, e quanto se ne discosta il risultato automatico, sta in
[`art/RITOCCHI-A-MANO.md`](art/RITOCCHI-A-MANO.md). È il motivo per cui
`art/plates/` è versionata e non solo rigenerabile.

## Il testo del gioco: di Weather Factory

L'inglese originale di BOOK OF HOURS e del DLC HOUSE OF LIGHT è loro. Qui
compare come **chiave** del dizionario in `translations/it.json`: il sistema di
locmod è costruito così, ogni resa italiana è indicizzata dalla frase inglese
che sostituisce, e senza quelle chiavi il mod non si può né costruire né
correggere.

`mod/BookOfHours_italian/loc/_origignal_from_core/` è invece una **copia di
comodo** del testo del gioco, tenuta a portata di mano per i confronti. Nessuno
strumento la legge — `apply.py` va a prendere i file dal gioco installato — e
resta un punto su cui la clausola «all or a substantial part of our writing»
merita attenzione.

## La traduzione italiana: mia, ed è della comunità

La resa italiana è mia, e il mod è pubblicato sul Workshop col tag
`Community Translation`. **Ufficiale è il sistema di locmod, non questa
traduzione**: Weather Factory non l'ha commissionata, rivista né approvata.

## Il mod francese: di chi l'ha fatto

`mod/BookOfHours_italian/loc/_mod_in_french/` serve come riferimento a chi
traduce e sta sul disco di chi ci lavora, ma **non è in questo repository**: è
lavoro di un altro modder, e né la licenza di Weather Factory né la mia lo
coprono. Si recupera da [Nexus](https://www.nexusmods.com/bookofhours/mods/42).

## Il font: EB Garamond, OFL

`art/font/` contiene EB Garamond sotto SIL Open Font License 1.1. La licenza sta
accanto ai file, in [`art/font/OFL.txt`](art/font/OFL.txt).

---

BOOK OF HOURS e HOUSE OF LIGHT sono di Weather Factory Ltd. Questo progetto non
è affiliato a Weather Factory.
