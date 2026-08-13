# Korak 0 prije Faze 5.2 — kontrola N-22, higijena, inventar za UI

> ✅ **Sekcija A je od tada IZVEDENA.** Presuda „sustav podnosi 1 istovremenu predaju“
> potvrđena je i popravljena: errata **#62** (gubitak predaja) i **#63** (nesklad
> odustajanja i upisa), oboje mergeano u `main` (PR #28). Rečenica „ne popravljam ništa“
> u §A.3 opisuje stanje **tog koraka**, ne današnje — v. `docs/fix-62-63-wrapup.md`.

**Datum:** 2026-08-12 · **Grana:** `faza-5-hintagent` · **Status:** mjerenje + inventar,
bez izmjena u `frontend/src/` i bez izmjena u `backend/`

---

# A — N-22: presuda

## A.0 🔴 Presuda

> **Sustav podnosi TOČNO JEDNU istovremenu predaju. Druga istovremena predaja se
> ODBACUJE — ne kasni, nego nestaje: ne nastaje redak u `attempts`, student čeka 15 s i
> dobije 504.**

**N = 1.** To **nije dovoljno** za 20 asinkronih sudionika. Uz tempo izmjeren iz
produkcijskih podataka, procjena gubitka je **~13 % predaja**, i to tiho.

🔴 **Nema veze s hintovima.** `coordinator.py` je byte-identičan `origin/main`-u i nije
diran od Faze 3E. Mjereno uz `USE_LLM_HINTS=false`. Kvar je zatečen; 5.1 ga je samo
otkrila jer je prva pokrenula paralelno opterećenje.

## A.1 Kontrolno mjerenje bez hintova

Harness: `n` niti, svaka svoj korisnik (concurrent pokušaji istog korisnika sudarili bi se
na `uq_attempts_user_task_number`), 8 zahtjeva po niti, isti zadatak i isti točan upit,
`threading.Barrier` za stvarni istovremeni start.

| n | zahtjeva | **uspjelo 200** | 504 | gubitak | p50 uspjelih | p95 uspjelih | max |
|---|---|---|---|---|---|---|---|
| 1 | 8 | 8 | 0 | 0 % | 125,0 ms | 191,3 | 191,3 |
| 2 | 16 | 15 | 1 | **6 %** | 119,3 ms | 148,8 | 148,8 |
| 3 | 24 | 21 | 3 | 13 % | 120,5 ms | 139,2 | 156,2 |
| 4 | 32 | 26 | 6 | 19 % | 121,4 ms | 142,5 | 148,8 |
| 6 | 48 | 33 | 15 | 31 % | 122,3 ms | 149,9 | 170,2 |
| 8 | 64 | 36 | 28 | **44 %** | 123,1 ms | 173,9 | 177,9 |

### A.1.2 Prag je OŠTAR, latencija NE raste

Prvi 504 pojavljuje se već pri **n = 2**. Ono što ga čini dijagnostički jednoznačnim:
**p50 uspjelih zahtjeva se ne mijenja** — 125 ms pri n=1, 123 ms pri n=8. Raspodjela je
**bimodalna**: ili ~120 ms, ili točno 15 000 ms. Ničega između.

Da je uzrok zasićenje ili red čekanja, latencija uspjelih bi rasla s n. Ne raste. Dakle
zahtjevi se ne čekaju — **nestaju**.

### A.1.3 Koji timeout puca

`GATEWAY_TIMEOUT = 15` ([config.py:63](backend/app/core/config.py#L63)), potrošen u
[routes.py:213](backend/app/api/routes.py#L213):

```python
result = await bridge.wait(cid, timeout=config.GATEWAY_TIMEOUT)
except (asyncio.TimeoutError, TimeoutError):
    raise HTTPException(status_code=504, detail="orchestration_timeout")
```

Izmjerene latencije neuspjeha: **15 012 – 15 070 ms**. Tijelo: `{"detail":
"orchestration_timeout"}`.

🔴 **To NIJE koordinatorov `evaluation_timeout`** (`DEFAULT_UPDATE_TIMEOUT = 5.0`, koji bi
dao `detail="evaluation_timeout"` nakon 5 s). Coordinator **nikad nije odgovorio** —
istekao je bridge Future u gatewayu. Nije uvicorn: uvicornov default keep-alive nije
dosegnut, a odgovor dolazi iz naše rute s našim `detail` nizom.

### A.1.4 Uspjeh nije degradiran, nego binaran

Traženo je razlikovati „200 sa 3 s kašnjenja" od 504. Takvih nema: **nijedan uspjeli
zahtjev ni na jednoj razini nije prešao 192 ms.** Degradacije nema — ima gubitka.

## A.2 Uzrok

### A.2.1 Iz koda

[coordinator.py:178-209](backend/agents/coordinator.py#L178-L209), `_recv_matching`:

```python
if msg_ont == ontology and (cid is None or msg_cid == cid):
    return msg
_log.debug("Coordinator: drained stale poruka (...)")   # ← poruka se ODBACUJE
```

FSM u `UPDATE` čeka `model-updated` s **cid-em tekućeg flowa**. Svaka druga poruka u
mailboxu — uključujući `submit-attempt` **drugog studenta** — pada u `else` granu i biva
**trajno odbačena**.

Dokumentirani invarijant ([coordinator.py:29-31](backend/agents/coordinator.py#L29-L31)):

> „svaka ne-self.cid poruka je nužno MRTVA (od prethodnog timeoutanog flowa), nikad
> buduća — pa je drop siguran"

🔴 **Ta tvrdnja ne stoji.** Vrijedi samo ako zahtjevi stižu strogo jedan po jedan. Čim dva
HTTP klijenta predaju istovremeno, odbačena poruka je **budući** zahtjev, ne mrtvi. Komentar
predviđa pad invarijanta tek „ako se uvede dispatcher" — zapravo pada već kod **konkurentnih
HTTP klijenata**, kojih ima od Faze 3E.3.

### A.2.2 Iz mjerenja — oštro predviđanje koje se moglo oboriti

Iz mehanizma slijedi: u rafalu od K **istovremenih** predaja prvi ulazi u flow, ostalih
K−1 stiže dok je FSM u EVALUATE/UPDATE i biva odbačeno. Predviđanje: **točno 1 uspjeh,
neovisno o K.**

| K istovremenih | rafala | zahtjeva | uspjelo | **uspjeha po rafalu** | neuspjeh |
|---|---|---|---|---|---|
| 2 | 3 | 6 | 3 | **1,0** | 504 × 3 |
| 3 | 3 | 9 | 3 | **1,0** | 504 × 6 |
| 4 | 3 | 12 | 3 | **1,0** | 504 × 9 |
| 8 | 3 | 24 | 3 | **1,0** | 504 × 21 |

Dvanaest rafala, dvanaest uspjeha — **nikad dva**. Predviđanje bi palo na bilo kojem
rafalu s dva uspjeha; nije palo.

### A.2.3 🔴 Odbačeno, ne odgođeno — potvrda kroz `attempts`

Rafal od 4 istovremene predaje, brojanje redaka u `attempts` prije i poslije (+3 s):

```
HTTP kodovi: [200, 504, 504, 504]
attempts redaka nastalo: 1 od 4 predaja
```

Tri predaje **nisu evaluirane**. Da su bile odgođene, red bi nastao kasnije. Nije.
Posljedica: nema BKT osvježenja, nema XP-a, nema traga u povijesti — studentov rad je
nestao bez zapisa igdje osim u `agent_messages_log`.

### A.2.4 Trajanje jednog prolaza

Jedan `RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND` traje **~120–130 ms**
(p50 uspjelih; HTTP round-trip uključen, pa je FSM prozor nešto kraći).

Gornja granica po zahtjevu **nije** 5 s iz `statement_timeout`, nego zbroj: sandbox
`statement_timeout = 5 s` + `DEFAULT_UPDATE_TIMEOUT = 5.0` + `DEFAULT_RECOMMEND_TIMEOUT = 5.0`.
Jedan patološki flow može držati FSM ~15 s, u kojem bi prozoru **sve** tuđe predaje bile
odbačene.

### A.2.5 Koliko studenata prije 504 — brojka

Ranjivi prozor je T ≈ 0,13 s po predaji. Tempo je izveden iz **stvarnih** podataka
(`attempts`, razmaci između uzastopnih predaja istog korisnika, < 1 h):

| mjera | vrijednost |
|---|---|
| medijan razmaka | **19,0 s** |
| p25 / p75 | 2,6 s / 39,8 s |
| uzorak | 30 razmaka, **2 korisnika** |

Uz `n` sudionika, λ = n / 19 s⁻¹, gubitak ≈ 1 − e^(−λT):

| sudionika | procijenjen gubitak predaja |
|---|---|
| 2 | ~1,4 % |
| 5 | ~3,4 % |
| 10 | ~6,6 % |
| **20** | **~12,8 %** |
| 30 | ~18,6 % |

🔴 **Ograda:** uzorak za tempo je tanak (2 korisnika, 30 razmaka) i procjena stoji ili
pada s njim. Ono što **ne ovisi** o procjeni je izmjereni pod: **kod dvije stvarno
istovremene predaje jedna se gubi uvijek** (12/12 rafala).

## A.3 🔴 STANI I JAVI — presuda i posljedica

**„Sustav podnosi 1 istovremenu predaju; iznad toga tiho odbacuje višak i vraća 504
nakon 15 s."**

Za 20 asinkronih sudionika **nije dovoljno**. Uz to, gubitak nije samo UX problem nego
**prijetnja valjanosti evala**: izgubljena predaja ne postoji ni u `attempts`, pa
analiza ne može ni znati da je bilo pokušaja. Podaci ne izgledaju oštećeno — izgledaju
kao da se manje predavalo.

**Ne popravljam ništa** (dira `coordinator.py`, odluka 8). Popravak je vlastita grana
prije deploymenta, ne dio 5.2. Skica opcija, bez odluke:

| opcija | opseg | rizik |
|---|---|---|
| per-request `OneShotBehaviour` umjesto jednog FSM-a | velik — FSM se rastavlja | mijenja arhitekturu koju rad opisuje |
| pravi correlation-router umjesto drop-a (guard postaje red) | srednji — `_recv_matching` + mailbox | invarijant iz komentara postaje istinit |
| N instanci Coordinatora + round-robin | mali kod, veći deployment | i dalje ograničeno na N |
| ostaviti + serijalizirati na klijentu (jedan zahtjev po sudioniku) | najmanji | ne pomaže kod 20 neovisnih preglednika |

**Posljedica za UI (5.2):** `submitSlot === "gateway"` danas kaže „Evaluacija je predugo
trajala". To je **netočno** — predaja nije trajala, nego je odbačena. Tekst mora reći da
rješenje **nije zabilježeno** i da ga treba predati ponovno.

---

# B — Higijena

## B.1 Tag `push` — obrisan

`push` je pokazivao na `6941cfa` („fix(2b-1b): sandbox_runner log + meta_generate_yamls
pre-flight cost cap"), običan commit iz Faze 2B. Provjereno: **`git merge-base
--is-ancestor push main` prolazi** — commit je predak `main`-a i dostupan je iz najmanje
deset grana. Tag nije nosio nijedan checkpoint koji bi se izgubio; nastao je omaškom
(`git tag push` umjesto `git push`).

Obrisan lokalno (`git tag -d push`). 🔴 **Postoji i na remoteu**
(`git ls-remote --tags origin` ga vraća) — brisanje ondje pokreće korisnik:

```
git push origin :refs/tags/push
```

## B.2 Konvencija za povučene errata stavke — nije postojala, sada postoji

Praksa je postojala u dva primjera (`#49` umirovljen broj, `#60` povučen odjeljak unutar
valjanog nalaza), ali **nigdje kao pravilo** — pa je sljedeće povlačenje ovisilo o
sjećanju. Zapisana kao invarijanta
[„Povučena errata stavka se OZNAČAVA, nikad ne briše"](invarijante.md#povucena-errata):
broj ostaje, tekst se precrtava, oznaka `🔴 POVUČENO (datum)` nosi razlog i ono što
ostaje istinito.

## B.3 `scratchpad/`

**Nije** u `.gitignore` — ni u korijenskom ni u `backend/`. **Nije nikad ni commitan**
(`git log --all -- '*scratchpad*'` prazan), i u repou ne postoji takav direktorij; sav
privremeni materijal ovog rada živi u `/tmp/claude-*/…/scratchpad`, izvan stabla.

Rizik je hipotetski (netko kasnije napravi `./scratchpad`), pa **nisam dodavao unos** —
to bi bila izmjena bez povoda. Ako se želi preventivno, jedan redak u `.gitignore`.

---

# C — Inventar za 5.2

## C.1 🔴 Ugovor iz 5.1: backend DA, frontend NE

### C.1.1 U živom `openapi.json` — jest

| shema | polja |
|---|---|
| `MeResponse` | `id`, `username`, `email`, `role`, **`hints_enabled`** |
| `TaskDetailResponse` | …, `solved`, **`last_attempt_error_type`** |
| `HintResponse` | `hint_text`, `source`, `concept`, `remaining`, `next_refill_at` |
| `HintRequestBody` | `task_id` |
| path | **`/hint` → `post`** |

### C.1.2 `schema.d.ts` — NIJE regeneriran

```
git diff --stat main -- frontend/src/lib/api/schema.d.ts   → prazno
grep -c "hints_enabled|last_attempt_error_type|HintResponse" → 0
```

🔴 **Frontend ugovor je stariji od backenda.** To **nije propust 5.1** — plan 5.1 je
izrijekom tražio „nula izmjena u `frontend/`", pa je regeneracija bila izvan opsega.
**Propust jest** da wrapup 5.1 ta dva polja nije naveo kao isporučen ugovor koji čeka
frontend; §F je spominjao samo „UI za hint". Ovime se ispravlja.

### C.1.3 Točan preostali diff za 5.2

| # | promjena | gdje |
|---|---|---|
| 1 | `npm run gen:api` → `schema.d.ts` dobiva `/hint`, `HintRequestBody`, `HintResponse`, `MeResponse.hints_enabled`, `TaskDetailResponse.last_attempt_error_type` | generirano, ne ručno |
| 2 | `useHint` mutacija (`POST /hint`) | `src/hooks/` |
| 3 | hint slot iznad `FeedbackPanel`a | `TaskPage.tsx` |
| 4 | gumb „Zatraži hint" u akcijskom redu | `TaskPage.tsx:417` |
| 5 | brojač `remaining` (NE u natpisu gumba) | v. C.3.2 |
| 6 | dva `data-testid` | v. C.4.3 |

🔴 **Ništa od ovoga nije backend posao** — backend ugovor je zatvoren i izmjeren.
Ako 5.2 zatreba izmjenu na backendu, to je znak da je ugovor bio nepotpun, ne rutinski
dodatak.

## C.2 Sedam stanja — iz STVARNIH odgovora

Uhvaćeno protiv živog poslužitelja (200-ice bez ključa → katalog; `200 llm` iz §E 5.1):

| stanje | HTTP | tijelo |
|---|---|---|
| flag isključen | **503** | `{"detail": "hints_disabled"}` |
| zadnji pokušaj nije netočan | **409** | `{"detail": "hint_not_unlocked"}` |
| iscrpljen limit | **429** | `{"detail": "hint_rate_limited"}` |
| LLM pao **i** katalog prazan | **503** | `{"detail": "hint_unavailable"}` |
| LLM uspio | **200** | `{"hint_text": "…", "source": "llm", "concept": "…", "remaining": 4, "next_refill_at": "2026-08-12T16:47:34.964482Z"}` |
| katalog | **200** | `{"hint_text": "…", "source": "fallback", "concept": "null_handling", "remaining": 4, "next_refill_at": "…"}` |
| idempotentno ponavljanje | **200** | **bajt-identično prethodnom** — isti `hint_text`, isti `source`, isti `remaining`, isti `next_refill_at` |
| HintAgent ne odgovara | **504** | `{"detail": "hint_timeout"}` (nije izazvano uživo) |

### C.2.1 🔴 Dva različita UI stanja iz istog statusa

`503` nosi dva **suprotna** značenja i frontend ih **mora** razlikovati po `detail`, ne po
statusu:

| `detail` | značenje | UI |
|---|---|---|
| `hints_disabled` | značajka ne postoji na ovom poslužitelju | **gumb se TIHO SAKRIJE** — nikad ne postoji |
| `hint_unavailable` | značajka postoji, ovaj put nema savjeta | **gumb ostaje**, poruka „savjet nije dostupan", klik se smije ponoviti |

🔴 `hints_disabled` se u praksi **ne smije ni dogoditi** na klik: `MeResponse.hints_enabled`
stiže pri prijavi, pa se gumb sakriva prije prvog rendera. Ako ga korisnik ipak dobije,
to je signal da je flag promijenjen usred sesije — tretirati kao „sakrij gumb sada".

### C.2.2 Ponavljanje se ne razlikuje od novog hinta

Idempotentni odgovor je identičan izvornom. Frontend **ne može** razlikovati „upravo
generirano" od „vraćeno iz pohrane". Za UI je to uglavnom dobro (isti sadržaj = isti
prikaz), ali znači: **ne animirati dolazak hinta kao novost** i ne trošiti `remaining`
lokalno — brojka u odgovoru je autoritativna.

## C.3 Otključavanje i brojač

### C.3.1 Otključavanje — potvrđeno

`last_attempt_error_type` stiže u `TaskDetailResponse` → `useTask`
([useTask.ts:12](frontend/src/hooks/useTask.ts#L12)) → `queryKey: ["task", taskId]`, koji
`useSubmitAttempt` **već invalidira**
([useSubmitAttempt.ts:56](frontend/src/hooks/useSubmitAttempt.ts#L56)). Postojeći kanal,
bez ijedne izmjene. Prozor osvježavanja izmjeren u A3 (5.0): ~37 ms lokalno.

### C.3.2 🔴 STANI I JAVI — gdje žive `remaining` / `next_refill_at`

`HintResponse` ih nosi, ali to je odgovor na **već potrošen** zahtjev. Prije prvog klika
frontend ih nema.

| opcija | dodatni pozivi | diff u `schema.d.ts` | problem |
|---|---|---|---|
| `MeResponse` | 0 | +2 polja | `/me` je **identitet**, dohvaća se pri prijavi i rijetko osvježava; živ brojač ondje zastarijeva. `hints_enabled` je ondje ispravno jer je **konfiguracija poslužitelja** i ne mijenja se |
| `TaskDetailResponse` | 0 | +2 polja | brojač je **po korisniku**, ne po zadatku — duplicirao bi se u N cache unosa i bio zastario u svima osim tekućem |
| zaseban `GET /hint-credit` | **+1 po ekranu** | +1 path, +1 shema | još jedan poziv za dvije brojke |
| **`ProfileResponse` (preporuka)** | **0** | +2 polja | — |

**Preporučujem `ProfileResponse`.** Razlozi, redom po težini:

1. `/profile` **već je u cacheu na Task ekranu** — `SidebarCards` ga čita preko
   `useProfile`, a `SidebarCards` živi u `AppShell`u koji omata sve prijavljene ekrane.
   Nula dodatnih poziva, i to provjereno, ne pretpostavljeno.
2. Oblik podatka je isti kao ono što `/profile` već nosi: **stanje po korisniku koje se
   mijenja u vremenu** (xp, level, streak). Brojač hintova je isti rod.
3. `["profile"]` je **već** u `onSuccess` listi `useSubmitAttempt`
   ([:49](frontend/src/hooks/useSubmitAttempt.ts#L49)), pa je zahtjev iz §C.4 plana 5.0
   ispunjen bez ijedne nove invalidacije.
4. `MeResponse` ostaje čist identitet — konfiguracija (`hints_enabled`) da, živo stanje ne.

🔴 **Ovo je backend izmjena** (+2 polja na `ProfileResponse`), pa je ne izvodim ovdje.
Treba tvoja potvrda prije nego uđe u 5.2.

### C.3.3 Invalidacija nakon potrošenog hinta — potvrđeno i dopunjeno

Uz preporuku iz C.3.2 brojač čita `["profile"]`, koji `useSubmitAttempt` već invalidira →
zahtjev §C.4 plana 5.0 je zadovoljen (`refetchType: 'active'` default, a observer postoji
jer `SidebarCards` trajno čita taj key).

🔴 **Ali to nije dovoljno.** Kredit se ne troši predajom nego **hintom**, pa `useHint`
mutacija u svom `onSuccess` **mora** invalidirati `["profile"]`. Bez toga se brojka
osvježi tek pri sljedećoj predaji — student potroši hint i vidi staru brojku.

## C.4 Akcijski red — što 5.2 mjeri na živom ekranu

N-20 je mjeren na harnessu; ograda je bila da se ponovi kad gumb postoji.

### C.4.1 Mjerna matrica

Visina kartice editora (`Card` na [TaskPage.tsx:405](frontend/src/pages/TaskPage.tsx#L405))
i akcijskog reda ([:417](frontend/src/pages/TaskPage.tsx#L417)):

| širina | bez gumba (danas) | s gumbom `disabled` | s gumbom `enabled` |
|---|---|---|---|
| 768 px | referentna | mjeri | mjeri |
| 1280 px | referentna | mjeri | mjeri |
| 1920 px | referentna | mjeri | mjeri |

Traži se: **prelama li se red** (`flex-wrap` je već ondje) i **pomiče li se editor**.
Referentna vrijednost mora biti snimljena **prije** uvođenja gumba — ista lekcija kao
p95 baseline u 5.1.

### C.4.2 Natpis

Natpis mora biti **isti u oba stanja** (H3.8) i zamrznut je na **„Zatraži hint"**.
🔴 Brojač **nikad** u natpisu (§G7.2 / C.4 plana 5.0) — inače se natpis mijenja s brojkom
i H3.8 pada.

### C.4.3 `data-testid`

U `frontend/src/` danas **ne postoji nijedan** `data-testid`. 5.2 uvodi prva dva:

| testid | na čemu |
|---|---|
| `editor-box` | `div` s `h-[420px] … xl:h-[520px]` ([:408](frontend/src/pages/TaskPage.tsx#L408)) |
| `action-row` | `div.flex.flex-wrap…justify-end` ([:417](frontend/src/pages/TaskPage.tsx#L417)) |

## C.5 A11y — `aria-disabled` bez tooltipa

### C.5.1 Postoji li obrazac — djelomično

`aria-disabled` se u aplikaciji **ne koristi nigdje**. `aria-describedby` **postoji na
jednom mjestu**: [RegisterPage.tsx:152](frontend/src/pages/RegisterPage.tsx#L152), gdje je
polje vezano na vidljivi `<p id="username-pomoc" className="text-sm text-muted-foreground">`.

To je presedan za **„razlog kao vidljiv tekst, programatski vezan"** — i nosi već
riješeno pitanje kontrasta (`text-sm`, ne `text-xs`, jer je na snimci bio najslabiji
tekst na ekranu). 5.2 preslikava taj obrazac; **tooltip/`title` se ne uvodi** (H3.7).

### C.5.2 🔴 Klik na `aria-disabled` gumb

`aria-disabled` gumb **ostaje fokusabilan i klikabilan** — to je i svrha (za razliku od
`disabled`, čitač ekrana ga vidi i pročita razlog). Ali klik koji ne radi ništa i ne kaže
ništa je kvar.

Predloženo ponašanje, po redu:

1. `onClick` **ne šalje zahtjev** kad je zaključano — nula mrežnog prometa.
2. Umjesto toga **pomakne fokus** na vidljivi razlog (`aria-describedby` meta) i objavi ga
   kroz `aria-live="polite"` — student koji ne gleda taj dio ekrana svejedno dobije
   povratnu informaciju.
3. Ruta ostaje druga linija obrane: 409 `hint_not_unlocked` i dalje postoji jer je prozor
   između predaje i osvježenog `TaskDetailResponse`a stvaran (C.3 plana 5.0) — UI ga samo
   čini rjeđim, ne nemogućim.

### C.5.3 Kontrastni parovi za 5.2 (N-4, ne mjeri se sada)

| tekst | podloga |
|---|---|
| natpis gumba u `aria-disabled` stanju | `card` |
| razlog (`muted-foreground`) | `card` |
| `remaining` brojač | `card` |
| tekst hinta u slotu | podloga slota |

## C.6 Slot za hint

### C.6.1 `submitSlot` enum — potvrđen, redci pomaknuti

[TaskPage.tsx:224-232](frontend/src/pages/TaskPage.tsx#L224-L232) (ne `:337`):

```
pending → gateway (504) → infra → feedback → null
```

Komentar `:222` i dalje tvrdi „točno jedan slot renderira", i to i dalje vrijedi —
grane su međusobno isključive po v5 statusu. Render slotova:
[:441-471](frontend/src/pages/TaskPage.tsx#L441-L471).

### C.6.2 Gdje sjeda hint

Po `faza-4.7-korak-0.md` §D: **zaseban slot IZNAD `FeedbackPanel`a**, dakle između
akcijskog reda ([:417](frontend/src/pages/TaskPage.tsx#L417)) i lanca `submitSlot`
([:441](frontend/src/pages/TaskPage.tsx#L441)).

🔴 **Hint NE ulazi u `submitSlot` enum.** Enum je „točno jedan od stanja predaje"; hint je
neovisan i **koegzistira** s feedbackom — student traži hint upravo *nakon* što je vidio
feedback netočne predaje. Da uđe u enum, jedan bi istisnuo drugi.

Kad su oba prisutna: hint gore, feedback ispod, oba vidljiva. Redoslijed nije kozmetika —
hint je akcija koju je student upravo zatražio i mora biti bliže gumbu koji ju je pokrenuo.

---

# D — Entry / exit za 5.2

**Entry:** backend ugovor zatvoren i izmjeren (C.1.1) · `/profile` proširenje odobreno
(C.3.2) · referentne visine akcijskog reda snimljene prije gumba (C.4.1).

**Exit (mjerivo, ne opisno):**

1. `schema.d.ts` regeneriran; `git diff` pokazuje točno 5 dodataka iz C.1.3.
2. Svih 7 stanja iz C.2 ima svoj UI put; `hints_disabled` i `hint_unavailable` daju
   **različit** ishod na ekranu.
3. Gumb se ne renderira kad je `hints_enabled === false` — provjereno u DOM-u, ne okom.
4. Natpis identičan u oba stanja; brojač nije u natpisu.
5. Klik na zaključan gumb: **0 mrežnih zahtjeva**, fokus na razlogu.
6. `useHint.onSuccess` invalidira `["profile"]`; brojač se osvježi bez reloada.
7. Visina akcijskog reda na 768/1280/1920 izmjerena i uspoređena s referentnom.
8. Kontrastni parovi iz C.5.3 izmjereni.
9. Hint i feedback **istovremeno vidljivi** kad oba postoje.

**Izvan opsega 5.2:** ~~popravak N-22 (vlastita grana)~~ ✅ izveden — errata #62 + #63;
N-21 (`submitted_query` u FIPA logu) i dalje otvoren.
