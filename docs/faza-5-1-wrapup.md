# Faza 5.1 — HintAgent iza flaga, bez UI-ja (wrapup)

**Datum:** 2026-08-12 · **Grana:** `faza-5-hintagent` · **Prethodnik:** `faza-5-0-preduvjeti`

Šesti SPADE agent isporučen, ruta `POST /hint` radi kroz živi FIPA lanac, značajka
stoji iza `USE_LLM_HINTS=false`. Frontend nije diran — ovo je backend ugovor koji UI
tek dolazi konzumirati.

---

## A — Isporučeno

| commit | sadržaj |
|---|---|
| `1b5e00b` | **B1** — `attempts.sqlstate` se popunjava kroz `sandbox_runner → evaluation → evaluator_agent` |
| `4571e6b` | **C** — `build_hint_payload`, bijela lista po `error_type`, guard nad 80 zadataka × 7 tipova |
| `8b83207` | **D1 (dio)** — runtime LLM klijent (`max_retries=0`, eksplicitan timeout) + config |
| `eaea3ca` | **D1–D4** — HintAgent, `POST /hint`, telemetrija, redigirano logiranje |

**Novih testova:** 29 (`test_hint_logic.py` 15, `test_hint_route.py` 14).
**Puna suite:** 737 prošlo, 1 preskočeno. Nula regresija.

🔴 **Zamrznute datoteke poštovane:** `git diff --stat origin/main -- agents/coordinator.py
agents/persistence.py` daje prazan izlaz. `git status --short frontend/` prazan.

### Lanac

```
POST /hint → bridge.register() → gateway --request-hint--> HintAgent
                                              ↓ (to_thread: DB → LLM → katalog → upis)
             bridge.resolve() <-- gateway <--inform/failure--
```

HintAgent **ne ulazi u Coordinatorov FSM** (§B.4.4): FSM je globalno serijaliziran,
LLM poziv traje ~2,8 s (izmjereno), pa bi kroz njega svaka tuđa `POST /attempt` čekala
taj poziv.

---

## B — Exit kriteriji (§E), izmjereno

Sva mjerenja su na živom poslužitelju sa **stvarnim** LLM pozivima osim gdje piše
drukčije. Suite ih ne ponavlja — ondje je SDK mockan, pa `pytest` ne troši novac.

| # | kriterij | izmjereno | ✅ |
|---|---|---|---|
| 1 | `/hint` vraća hint na živom lancu | 200, `source="llm"`, 2830 ms | ✅ |
| 2 | s `USE_LLM_HINTS=false` → 503 `hints_disabled`, **bez odlaznog poziva** | 503; **0 veza** na brojaču (v. §C.3) | ✅ |
| 3 | `hints` READ-ONLY u runtimeu | `count(*)` = 32 prije i poslije **svake** faze, uklj. 10 hintova (5 LLM + 5 katalog) | ✅ |
| 4 | zadatak bez netočnog pokušaja → 409 | 409 `hint_not_unlocked` bez pokušaja **i** nakon točnog rješenja | ✅ |
| 5 | fallback dokazan gašenjem ključa | poslužitelj bez `ANTHROPIC_API_KEY` → 200, `source="fallback"`, `hint_id=13` | ✅ |
| 6 | 429 na iscrpljen limit | kodovi redom `200,200,200,200,429` | ✅ |
| 7 | **`POST /attempt` p95 nepromijenjen pod 3 paralelna hinta** | **134,1 ms** (baseline 137,3 · kontrola 135,2) | ✅ |
| 8 | guard §G2.3 nad svih 80 aktivnih zadataka | u suiteu, 80 × 7 tipova | ✅ |
| 9 | `agent_messages_log` bez `hint_text` i bez `submitted_query` | 68 redaka od `hint@`: **0** sadrži išta od toga (v. nalaz N-21) | ✅ |
| 10 | 10 hintova → 10 redaka u `hint_requests`, svaki na netočan pokušaj | 10/10, `is_correct=false` provjeren kroz FK | ✅ |
| 11 | `coordinator.py` byte-identičan | prazan `git diff` | ✅ |
| 12 | idempotencija: dva klika → jedan poziv | isti tekst, `remaining` nepromijenjen, 1 redak | ✅ |

### B.1 p95 — tri mjerenja, ne jedno

„Nepromijenjen" je usporedba, pa je trebalo troje:

| mjerenje | p95 | p50 | stdev | n |
|---|---|---|---|---|
| **baseline** — proces BEZ HintAgenta | 137,3 ms | 121,1 | 6,6 | 40 |
| **kontrola** — HintAgent u procesu, nula hintova | 135,2 ms | 127,1 | 6,9 | 40 |
| **pod opterećenjem** — 3 stvarna hinta istodobno | **134,1 ms** | 125,4 | 5,9 | 40 |

Razlike (−2,1 i −1,1 ms) su unutar standardne devijacije samog mjerenja (~6 ms), dakle
nerazlučive od šuma. Nula grešaka na `/attempt`, 6/6 hintova posluženo.

🔴 **Baseline je morao biti snimljen prije D1** i jest — retroaktivno se ne može, jer
nakon što agent uđe u proces čistog stanja više nema.

🔴 **Ovo je svojstvo lokalnog mjerenja, ne svojstvo sustava.** Jedan stroj (WSL2), jedan
proces, jedan mjerni klijent, `n=40`. Ne govori kako se sustav ponaša pod stvarnim
brojem korisnika. Ista ograda koja stoji uz 37 ms iz A3 (5.0 §D).

---

## C — Odstupanja od plana, sa razlozima

### C.1 `source="rule"` → `source="fallback"`

§B.4.2 plana 5.0 propisuje HTTP tijelo sa `source="rule"`, dok `ck_hint_requests_source`
u bazi dopušta `'llm' | 'fallback' | 'unavailable'`. **Ujednačeno na `fallback` u oba.**

Dvije riječi za istu stvar su točno mehanizam NALAZA N-8. CHECK je već migriran i
isporučen, HTTP niz nije, i `frontend/` ga još ne konzumira — pa je jeftinija strana
promijenjena.

### C.2 `refuse` nema proizvođača

§B.4.2 predviđa `Hint → gateway: refuse` za iscrpljen limit. §D2 propisuje da limit
provjerava **ruta**, prije buđenja agenta. Ruta je pobijedila: 429 se tako vraća bez
XMPP round-tripa, a `remaining` se ionako računa u ruti (C.4).

Posljedica: `Performative.REFUSE` i dalje nema nijednog potrošača. To je uredno — skup
je definiran kao FIPA-ACL podskup, ne kao popis korištenog.

### C.3 `hint_requests` piše AGENT, ne ruta

Plan ne propisuje pisca. Izabran je agent: ako HTTP klijent odustane (504, zatvorena
kartica), **poziv je već plaćen**, a zapis u ruti bi ga izgubio i telemetrija bi
podbrojila potrošnju.

### C.4 Redak se piše samo za POSLUŽENE zahtjeve

`llm` / `fallback` / `unavailable` ostavljaju redak. **Odbijanja ne ostavljaju**
(503 `hints_disabled`, 409, 429) — takav zahtjev nikad nije ušao u posluživanje, a
redak bi tvrdio „pokušali smo i nismo imali što dati", što nije istina.

🔴 Ovo je tumačenje upute „upiši na svaki ishod, uključujući 503": 503 koji dobiva
redak je `hint_unavailable`, ne `hints_disabled`. Ako je namjera bila šira, ovo je
mjesto koje se mijenja.

### C.5 Idempotencija ne ponavlja `unavailable`

Redak sa `source='unavailable'` ostaje u telemetriji, ali se **ne vraća** kao odgovor.
Inače bi jedan pad providera trajno zaključao hint na tom pokušaju.

### C.6 Mrežni trag nije paketni

Exit traži dokaz „mrežnim tragom, ne pretpostavkom". **`tcpdump` ni `strace` nisu
instalirani** na ovom stroju.

Umjesto toga: SDK je preusmjeren (`ANTHROPIC_BASE_URL`) na lokalni slušatelj koji broji
prihvaćene TCP veze.

| slučaj | veza zabilježeno |
|---|---|
| `USE_LLM_HINTS=false` | **0** |
| `USE_LLM_HINTS=true` (pozitivna kontrola) | **1** |

Pozitivna kontrola je ono što nuli daje značenje — bez nje bi „0 veza" moglo značiti
samo da brojač ne radi. Jedna veza uz uključen flag usput potvrđuje i `max_retries=0`.

**Ograda:** ovo je slabije od paketnog traga jer vidi samo veze prema adresi koju smo
sami podmetnuli. Ne isključuje odlazni promet nekim drugim putem — samo pokazuje da
kôd koji bi taj poziv napravio nije bio izvršen.

### C.7 Eksperiment za p95 morao se prepraviti

Prva izvedba je pala u 504. Radnici su uz hint slali i **vlastite** `POST /attempt` da
otključaju pokušaj, pa su kroz serijalizirani Coordinator FSM tekla četiri paralelna
`/attempt` zahtjeva. Dva uzroka, jedan broj — iz toga se ne bi moglo zaključiti je li
kriv hint.

Ispravak: otključavajući pokušaji se stvaraju **prije** mjerenja; tijekom mjerenja
radnici šalju isključivo `POST /hint`. Tek tada je hint jedina dodana varijabla.

---

## D — Nalazi

### N-21 — `submitted_query` je u `agent_messages_log` od Faze 3 (zatečeno)

| mjera | vrijednost |
|---|---|
| redaka u `agent_messages_log` | 7480 |
| redaka koji sadrže `submitted_query` | **1568** |
| raspon | 2026-07-20 → danas |
| redaka od `hint@localhost` | 68 |
| **od toga sa `submitted_query`** | **0** |

Hint put je čist — otvoreno šalje `{user_id, task_id}`, natrag `{task_id, source,
hint_len}`. Ali **put `POST /attempt` upisuje studentov upit u trajni log** i to radi
od Faze 3, prije 5.1.

To 5.1 nije uveo i nije popravio. Bitno je jer:
- `export_eval_data.py` pseudonimizira `user_id`, ali sadržaj upita ne dira,
- privola (5.0 §D) govori o obradi podataka, a ovo je trajna pohrana doslovnog rada.

**Status: OTVORENO.** Ne popravlja se u 5.1 jer bi tražilo dirati `base.py` i
`coordinator.py` (zamrznuti odlukom 8). Kandidat za Fazu 6 ili errata.

### N-22 — 4 paralelna `POST /attempt` → 504 (opažanje, nije izolirano)

> ✅ **RIJEŠENO nakon ovog wrapupa.** Kontrolno mjerenje pripisalo je uzrok Coordinatoru
> (errata **#62**), a uz njega je nađen i zaseban kvar **#63**. Oba su popravljena i
> mergeana u `main` (PR #28). Tekst ispod ostaje **nepromijenjen kao povijesni zapis**
> stanja u kojem uzrok još nije bio pripisan — v. `docs/fix-62-63-wrapup.md`.

U prvoj (pokvarenoj) izvedbi §C.7 tri radnika + mjerni klijent slali su `/attempt`
istodobno; dio je vraćao 504 `orchestration_timeout`.

🔴 **Ovo NIJE zaključak da hint uzrokuje 504.** Hint i konkurentnost su ondje bili
pomiješani, a kontrolno mjerenje s 4 paralelna `/attempt` **bez ijednog hinta** nije
izvedeno. Opažanje je u skladu s GATE 2 odlukom (`coordinator.py:20-25`: jedan FSM,
globalna serijalizacija), ali pripisivanje uzroka traži vlastiti eksperiment.

Zapisano da se ne izgubi. **Status: OTVORENO**, za Fazu 6.

---

## E — Potrošnja LLM-a

| stavka | vrijednost |
|---|---|
| model | `claude-haiku-4-5` ($1,00 / $5,00 po MTok) |
| ulaz po pozivu (izmjereno `count_tokens`om) | 386 tokena |
| trošak po pozivu | ~$0,00089 |
| **stvarnih poziva u mjerenjima** | **14** |
| **ukupan trošak** | **~$0,012** |

Procjena prije mjerenja bila je ~45 poziva / $0,04 — stvarnost je ispala tri puta
jeftinija jer fallback i flag-off faze ne zovu providera uopće.

**Poziva u `pytest` suiteu: nula.** Svi testovi mockaju SDK; `make preflight` ne troši
kredit ni na jednom pokretanju.

🔴 **Prompt caching se NE koristi i ne treba ga dodavati:** minimalni keširajući prefiks
za Haiku 4.5 je 4096 tokena, a naš je 386 — `cache_control` bi se tiho ignorirao.

---

## F — Što ostaje otvoreno

| # | stavka | gdje |
|---|---|---|
| 1 | UI za hint (gumb, brojač, „tiho sakrij" kad `hints_enabled=false`) | Faza 5.2 |
| 2 | ERRATA #59 — privola je informirana, ali nije **zabilježena** | odluka korisnika |
| 3 | N-21 — `submitted_query` u trajnom FIPA logu | Faza 6 |
| 4 | ~~N-22 — 504 pod 4 paralelna `/attempt`~~ → ✅ errata #62 + #63, mergeano | — |
| 5 | `USE_LLM_HINTS` ostaje `false` u `.env` | namjerno |

🔴 **Za rad (C.5):** broj traženih hintova **nije mjera potražnje** — odozgo je ograničen
dizajnom (5 / 4 h). Ta rečenica mora stajati svugdje gdje se brojka spominje.
