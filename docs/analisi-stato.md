# BOOK OF HOURS — stato della localizzazione italiana

Analisi del 20 agosto 2026. Tutti i numeri sono prodotti dagli script in `tools/`
e sono riproducibili.

## Fonti confrontate

| | percorso | versione |
|---|---|---|
| Originale inglese | `steamapps/common/Book of Hours/bh_Data/StreamingAssets/bhcontent/core` | build installata |
| Mod italiano (tuo) | `~/.var/app/com.valvesoftware.Steam/.config/unity3d/Weather Factory/Book of Hours/mods/BookOfHours_italian` | 0.1.0 |
| Mod spagnolo | Steam Workshop `1028310/3784793429` (Mrdynamite) | 0.0.7 |
| Mod francese | copia in `loc/_mod_in_french` dentro il mod italiano | — |

Volume totale dell'originale: **7.725 entità in 175 file, 17.926 stringhe traducibili, 276.660 parole**
(include il DLC *House of Light*, i cui file stanno in `core` col prefisso `DLC_HOL_`).

## 0. Il fatto che condiziona tutto il resto

Il mod italiano **non è tradotto**: i file in `loc/loc_it` sono copie dei file
inglesi di `core`.

| | stringhe tradotte davvero | parole |
|---|---|---|
| Italiano | 124 / 17.926 — **0,7 %** | ~2.007 — **0,73 %** |
| Spagnolo | 17.573 — 98,0 % | ~276.186 — 99,83 % |
| Francese | 17.037 — 95,0 % | ~275.255 — 99,49 % |

Delle 124 stringhe italiane, **86 stanno in `decks/`**, che secondo il kit ufficiale
*non vengono mostrate in gioco*. In pratica il testo italiano visibile nei contenuti
è circa **38 stringhe**.

L'unica parte realmente localizzata è l'interfaccia: **292 UI labels** in
`content/cultures/culture.json`. Questo spiega esattamente la percezione di
incoerenza: menu e pulsanti in italiano, tutto il resto del gioco in inglese.

## 1. Tag, token e impostazioni — confronto tecnico

### Integrità del markup

Copertura onesta del controllo: verifica solo le stringhe effettivamente tradotte.

| | stringhe controllate | problemi |
|---|---|---|
| Italiano (contenuti) | 124 su 17.926 | nessuno |
| Italiano (UI labels) | 262 su 295 | nessuno |
| Spagnolo | 17.573 | 34 tag alterati (quasi tutti `<i>` aggiunti di proposito sui titoli) |
| Francese | 17.037 | 10 tag alterati, 7 a-capo divergenti, **1 token rotto** |

Il bug francese da non imitare: in `hint.workstation` hanno tradotto il token
`[further]` in `[plus loin]`. È un segnaposto sostituito dal motore: tradotto,
resta a schermo come testo letterale.

I `$`, i `{SETTING:kb…}` e i `<size=12px><smallcaps>` sono intatti in tutte e 292 le
UI labels italiane.

### Impostazioni divergenti — due problemi reali

**a) `fontscript` sbagliato.** L'italiano dichiara `"fontscript": "latinplus"`,
lo spagnolo `"latin"`.

Verificato negli asset del gioco (`sharedassets`): `latinplus` mappa su
`LatinABExtendedXNotoSans-Regular`, cioè **Noto Sans**, un sans-serif. `latin` mappa
su `EBGaramond08-Regular`, il serif usato da tutto il resto del gioco.
Con `latinplus` l'italiano viene reso in un carattere visibilmente estraneo.

`latin` è la scelta corretta: la Localisation Reference (riga 416) dice che Weather
Factory ha già aggiunto `ì`, `ò`, `ù` all'atlante latino *proprio per l'italiano*, e
lo spagnolo rende `á é í ó ú ñ ¿` senza problemi sotto `latin`.

**b) Due file cultura in conflitto.** `content/cultures/` contiene sia `culture.json`
sia `Italian.json`, entrambi con `"id": "it"` e 292 label, ma **due valori divergenti**:

| chiave | `Italian.json` | `culture.json` |
|---|---|---|
| `UI_BUGS_AND_ISSUES` | `<size=20>BUG E PROBLEMI?</size>` | `BUG E PROBLEMI?` |
| `UI_OPTIONSTITLE` | `<size=20>Impostazioni</size>` | `Impostazioni` |

Quale dei due vinca dipende dall'ordine di lettura. Va tenuto un file solo.
(Anche lo spagnolo ne ha due, ma identici — ridondanti, non dannosi.)

### Label mancanti e label morte

- **7 chiavi inglesi assenti dall'italiano** → in gioco restano in inglese.
  `UI_MODS` (già segnalata nel `Player.log`), `UI_USE_GAMEPAD` + tooltip,
  `UI_EDGE_SCROLL_AREA_*` (4). Solo `UI_MODS` è tradotta dallo spagnolo: le altre 6
  mancano anche lì, sono aggiunte recenti del gioco.
- **4 chiavi italiane assenti dal `culture.json` inglese.** Verificate anche contro le
  localizzazioni ufficiali `ru`, `jp`, `zh-hans` presenti nel gioco:

  | chiave | en | ru | jp | zh-hans | verdetto |
  |---|---|---|---|---|---|
  | `UI_DLC_COMING_SOON` | no | sì | sì | sì | **viva** |
  | `UI_ALTERNATIVE_STARTS_BLURB` | no | sì | sì | sì | **viva** |
  | `UI_MODS_INTRODUCTION` | no | no | sì | sì | **viva** |
  | `UI_DLC_AND_MODS` | no | no | no | no | morta |

  Tre su quattro sono chiavi reali che l'inglese non dichiara ma il gioco usa: vanno
  tenute. Solo `UI_DLC_AND_MODS` non compare in nessuna localizzazione ufficiale.

### Lunghezze

Il testo va in pulsanti a larghezza fissa, quindi conta la lunghezza *visibile*
(senza tag né token).

- rapporto medio italiano/inglese: **1,20**
- rapporto medio spagnolo/inglese: **1,33**

L'italiano è **più conciso dello spagnolo**: sulle lunghezze non c'è un problema
sistemico, e lo spagnolo non è un buon modello di brevità
(`UI_NEXTCOMPLETE`: EN "Go To Next Completed" → ES "Ir a la siguiente receta completada",
IT "Vai al Prossimo Completato").

66 label su 262 superano l'inglese di oltre il 30 %. Da rivedere a schermo, non a
tavolino, partendo dalle più estreme: `UI_HINT` (×2,60), `UI_AUTOSORTOVERLAP_NONE`
(×2,30), `UI_KEEPSAVE` (×2,22), `UI_FONT_SIZE` (×2,22), `UI_SAVES` (×2,00).

## 2. Qualità — dove l'italiano è davvero incoerente

Sulle 292 UI labels, la resa è buona e spesso migliore dello spagnolo. Il problema
non è la lingua, è la **mancanza di una convenzione applicata in modo uniforme**.

### Maiuscole nei titoli: l'italiano è incoerente con se stesso

| | Title Case anglosassone | stile frase | valutabili |
|---|---|---|---|
| Italiano | **22** (33 %) | 44 | 66 |
| Spagnolo | 3 (4 %) | 73 | 76 |

Al netto dei nomi propri del gioco — che anche lo spagnolo capitalizza (Soglia,
Albero delle Sapienze, Brancrug, Alba) — restano **18 label** in cui la maiuscola è
un puro anglicismo di stile:

| chiave | italiano attuale | spagnolo |
|---|---|---|
| `UI_KB_STACKCARDS` | Auto-Ordina Tutti i Vassoi | Ordenar automáticamente todas las bandejas |
| `UI_OPT_CONTRAST` | Modalità Alto Contrasto | Modo de alto contraste |
| `UI_OPT_AUTOSAVEINTERVAL` | Intervallo Salvataggio Automatico | Intervalo de guardado automático |
| `UI_OPT_DISABLE_SEASONALS` | Disabilita Contenuti Stagionali | Desactivar el contenido de temporada |
| `UI_OPT_INFODURATION` | Durata Notifiche Popup | Duración de las notificaciones emergentes |
| `UI_OPT_ACCESSIBLE_CARDS` | Testo Carte Accessibile | Texto accesible en las cartas |
| `UI_ZOOM_STEP_STEAMDECK` | Sensibilità Zoom Touchscreen | Sensibilidad del zoom en la pantalla táctil |
| `UI_KB_SLOWER` / `UI_KB_FASTER` | Velocità: Più Lento / Più Veloce | Velocidad: reducir / aumentar |
| `UI_SUSPICIOUS_SAVE` | Un Salvataggio Strano? | ¿Una partida peculiar? |
| `UI_FURTHERFILES` | Vedere Carte Nascoste? | ¿Ver documentos ocultos? |
| `VSYNC_0` | VSync + Limite di Frame | VSync + límite de fotogramas |
| `UI_KB_TRAY1`…`TRAY4` | Memorie / Anima / Abilità / Varie Apri/Chiudi | Abrir/cerrar Recuerdos / Alma / … |

Lo spagnolo ha scelto lo stile frase e lo applica quasi sempre (4 % di eccezioni
contro il 33 % italiano) — ed è la scelta giusta anche per l'italiano.

Nota metodologica: un primo conteggio dava 75 label in Title Case, ma era falsato.
Il filtro scartava le parole di ≤3 lettere prima di individuare la prima parola, e
questo penalizza l'italiano (i cui verbi iniziali sono corti: Vai, Apri, Salva) e
scagiona lo spagnolo (le cui parole funzionali sono corte: Ir, al, de). Il metodo
corretto è in `tools/style2.py`; `tools/style.py` conserva quello vecchio.

Da correggere comunque: `UI_SAVEEXIT` "Salva e Esci" → "Salva ed esci".

### Apostrofi

26 label usano l'apostrofo tipografico `’`, 1 usa quello dritto `'`. Va scelto uno
stile solo. Lo spagnolo non ha apostrofi, ma usa i caporali `«»` per le virgolette,
coerentemente — l'inglese usa `'…'`. Anche per l'italiano vanno decise le virgolette
(«» oppure "") e applicate ovunque.

## 3. Termini da lasciare in inglese

Metodo: quando **francese e spagnolo, indipendentemente, lasciano la stessa cosa in
inglese**, è un segnale forte.

### 258 stringhe intere lasciate in inglese da entrambi

Ripartite in: `elements` 103, `settings` 62, `verbs` 52, `recipes` 33, `decks` 8.
Molte sono punteggiatura pura (`.`, `?`, `!`) o segnaposto. Le altre sono nomi propri.

### 32 termini che sopravvivono verbatim in tutti e tre — da non tradurre

Nomi propri di persone, luoghi e ordini:

`Numa` · `Hokobald` · `Numen` · `Spencer` / `Spencer Hobson` · `Vak` · `Ramsund` ·
`Killasimi` · `Sacra Solis Invicti` · `Tridesma Hiera` · `Henavek` · `Lyterion` ·
`Cracktrack` · `Uzult` · `Sacra Limiae` · `Rowenarium` · `Julian Coseley` ·
`Didumos` · `Pyrus Auricalcinus` · `Marakat` · `Asimel` · `Stymphling` ·
`Nillycant` · `Lalla Chaima` · `Eigengrau` · `Lord Franklin Bancroft` · `Moly` ·
`Constance Lee` / `MCO Constance Lee` · `Scrumpy` · `Pilchards` · `Amiranis Beteli`

Lista completa in `docs/glossario-non-tradurre.json`.

### 67 divergenze — qui la decisione è nostra

Francese e spagnolo seguono due filosofie opposte sul lessico inventato del gioco:

| termine | spagnolo | francese |
|---|---|---|
| Ereb, Fet, Phost, Shapt, Trist, Chor, Wist | adattati/tradotti | lasciati in inglese |
| Carapace | tradotto | lasciato |
| Mettle | tradotto | lasciato |
| Horomachistry | Horomaquia | Horomachie |
| Hushery | Silenciería | Mutisme |
| Skolekosophy | Escolecosofía | Skolekosophie |
| Ithastry | Itastría | Ithasisme |
| Nyctodromy | Nictodromía | Nyctodromie |
| The Bosk | Soto | Le Bosquet |
| Birdsong | Canto de las Aves | Chant d'Oiseau |

E i quattordici Principi (aspetti fondamentali), che entrambi traducono:

| EN | ES | FR |
|---|---|---|
| Lantern | Candil | Lanterne |
| Forge | Forja | Forge |
| Edge | Filo | Lame |
| Winter | Invierno | Hiver |
| Heart | Corazón | Cœur |
| Grail | Grial | Graal |
| Moth | Polilla | Phalène |
| Knock | Apertura | Heurtoir |
| Sky | Cielo | Ciel |
| Moon | Luna | Lune |
| Nectar | Néctar | Nectar |
| Rose | Rosa | Rose |
| Scale | Escama | Écaille |
| Sound | Sonido | Son |

**Da decidere prima di tradurre una sola riga**, perché ricorrono migliaia di volte:
i Principi si traducono (Lanterna, Forgia, Filo, Inverno, Cuore, Graal, Falena, …)?
Le Sapienze si adattano all'italiano (Oromachia, Illuminazione) o restano inglesi?
Il lessico inventato (Ereb, Fet, Phost…) resta invariato?

Nota metodologica: per il francese il segnale «lascia l'inglese» è ambiguo quando la
parola è omografa in francese (Forge, Rose, Nectar, Illumination). Nel dubbio vale la
tabella delle label qui sopra, non il conteggio sui corpi.

## Correzioni applicate

Fatte nel commit `Correzioni all'interfaccia italiana` e in quello successivo. Il
mod di lavoro è in `mod/BookOfHours_italian/`; quello installato in Steam non è
stato toccato.

1. `fontscript`: `latinplus` → `latin`. ✔
2. Eliminato `content/cultures/Italian.json`. ✔
3. Aggiunta `UI_MODS` e le 6 label di gamepad/scorrimento ai bordi mancanti:
   **la UI è ora completa, 295/295**. Rimossa solo `UI_DLC_AND_MODS`. ✔
4. Maiuscole in stile frase su **52 label** (18 a più parole + 34 a due parole). ✔
5. Virgolette doppie curve `“…”`, apostrofo tipografico. ✔
   (Prima avevo messo i caporali `«…»`, poi ritirati: non compaiono mai nel testo
   inglese, quindi non c'è prova che siano nell'atlante del font latino. Tutte le
   lettere accentate italiane — à è é ì ò ù È — invece ci sono.)
6. `UI_SAVEEXIT`: "Salva e Esci" → "Salva ed esci". ✔
7. Il link al Workshop puntava a Cultist Simulator (`718670`) invece che a
   Book of Hours (`1028310`). ✔

Nota sul conteggio delle maiuscole: il primo classificatore richiedeva almeno due
parole valutabili dopo la prima, e quindi saltava tutte le label di **due** parole
— proprio le più problematiche (`Carica Partita`, `Nessuna Sovrapposizione`).
Recuperate con `tools/style3.py`: 43 candidate, di cui 8 nomi propri da lasciare
(lo spagnolo li capitalizza allo stesso modo) e 34 da correggere.

**Copertura dei glifi verificata** (`tools/glyphcheck.py`): ogni carattere non
ASCII usato dall'italiano compare nel testo inglese, che gira sotto lo stesso
`fontscript: "latin"`. Nessun rischio di caratteri tofu.

Resta aperta `UI_LOADEDTITLE` «Bentornato, Bibliotecario»: non è un problema di
maiuscole ma di genere del protagonista. Vedi `convenzioni.md`.

## Strumenti

| script | scopo |
|---|---|
| `tools/bohloc.py` | lettore JSON tollerante (UTF-16, virgole finali, caratteri di controllo) + estrazione campi traducibili |
| `tools/coverage.py` | copertura IT/ES/FR rispetto all'originale |
| `tools/integrity.py` | tag, token, template, a-capo sui contenuti |
| `tools/uicheck.py` | tag, token, chiavi mancanti/morte e lunghezze sulle UI labels |
| `tools/style.py` | apostrofi, virgolette (conteggio maiuscole superato) |
| `tools/style2.py` | maiuscole senza bias + verifica chiavi contro ru/jp/zh-hans |
| `tools/donottranslate.py` | termini lasciati in inglese da FR ed ES |
| `tools/refine.py` | ripulitura dei falsi positivi con confini di parola |

Richiedono `json5`. I percorsi sono in cima a `bohloc.py`.
