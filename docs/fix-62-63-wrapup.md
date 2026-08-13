# #62 + #63 — popravak konkurentnosti Coordinatora (wrapup)

**Datum:** 2026-08-13 · **Grana:** `fix-coordinator-concurrency` (s `origin/main`, `64107c1`)
**Commitovi:** `846f241` (#62) · `23e2046` (#63) · **Tag:** `fix-coordinator-concurrency`

---

## A — Što je bilo pokvareno

| | #62 | #63 |
|---|---|---|
| simptom | 504 nakon 15 s | 504 nakon 5 s |
| što je u bazi | **ništa** | **pokušaj, BKT, XP** |
| uzrok | drain-loop odbacuje tuđi `correlation_id` | UPDATE prozor i `statement_timeout` oba 5 s |
| od kada | Faza 3E.3 (3 mjeseca) | Faza 3E.2b |

Oba su bila **zatečena** — `coordinator.py` nije bio diran od Faze 3E. Faza 5.1 ih je
otkrila jer je prva pokrenula paralelno opterećenje.

---

## B — #62: FSM po razgovoru

### B.1 Zašto zaustavljanje odbacivanja ne bi bilo dovoljno

Dva su problema stajala jedan iza drugoga:

1. `_recv_matching(cid=self.cid)` **odbacivao** je poruke s tuđim cid-em,
2. `self.agent._flow` je bio **jedan atribut** — i da su poruke stizale, Coordinator ih
   ne bi imao gdje držati.

Zato popravak dira oboje: korelaciju **i** mjesto za stanje.

### B.2 Mehanizam — predložak JEST router

SPADE `dispatch()` isporučuje poruku svakom behaviouru čiji predložak matcha (provjereno
u izvoru, `spade/agent.py`). Predložak prima i `correlation_id`, što je izmjereno prije
pisanja koda:

```
isti cid + ista ontologija : True
drugi cid                  : False
isti cid, druga ontologija : False
```

Dakle korelacijski router **već postoji** u SPADE-u i ne treba ga pisati. Posao koji u
gatewayu radi `AgentBridge._pending` ovdje radi sam predložak.

| komponenta | uloga |
|---|---|
| `_Intake` (CyclicBehaviour) | prima `submit-attempt`, otvara **vlastiti** FSM po predaji |
| `OrchestrationFSM(flow)` | EVALUATE → UPDATE → RECOMMEND → RESPOND → kraj; predložak vezan uz **svoj** cid |
| `_flows: dict[cid → …]` | registry živih tokova + granica |
| `on_end` | LEAK GUARD: odjava toka i uklanjanje behavioura, bezuvjetno |

🔴 **Prijem više nije stanje FSM-a.** Dok je bio, jedan razgovor u tijeku značio je da se
sljedeći ne može ni **primiti** — što je i bio cijeli kvar. FSM je time dobio četiri
stanja umjesto pet; sekvenca razgovora je nepromijenjena.

### B.3 Granica i što se na njoj događa

`MAX_CONCURRENT_FLOWS = 64`. Na granici predaja se **odbija eksplicitno**:
`refuse` + `coordinator_busy` → **HTTP 503**.

🔴 **503, a ne 504.** 504 znači „nismo stigli odgovoriti"; ovdje smo odgovorili odmah i
namjerno, pa ponovni pokušaj ima smisla. Tiho odbijanje na granici bilo bi #62
reproduciran na drugom mjestu — student bi opet čekao `GATEWAY_TIMEOUT` bez objašnjenja.

`Performative.REFUSE` je time dobio prvog proizvođača; dotad je bio definiran ali
nekorišten.

**Ako granice ne bi bilo,** gornju granicu ne bi postavljala memorija (tok je jedan dict
+ jedan behaviour) nego **Evaluator**: on je jedan `CyclicBehaviour` koji obrađuje jednu
poruku po prolazu, pa bi se svi tokovi nagomilali u njegovom redu i masovno padali u
`evaluation_timeout` — za studenta nerazlučivo od kvara. Granica pretvara „svi propadaju
tiho" u „neki dobiju jasan odgovor".

### B.4 Invarijanta koja je bila neistinita

Stari tekst (`coordinator.py:29-31`):

> „svaka ne-self.cid poruka je nužno MRTVA … nikad buduća — pa je drop siguran"

Novi tekst opisuje ponašanje koje **stvarno vrijedi**:

> Poruka koja ne matcha nijedan behaviour nužno je ZAKAŠNJELA — njezin je tok već
> završio i predložak mu je uklonjen. Živ tok UVIJEK ima registriran svoj predložak.

Uz nju stoji i **citat testa koji ju izvršava** (`tests/test_coordinator_concurrency.py`) —
prije nije imala nijedan.

**GATE 2 pada** kao opis sustava i prepisan je. Ostaje istinito: Recommender je i dalje
usko grlo, ali s **redom**, ne s gubitkom.

---

## C — #63: odustajanje i upis se ne mogu razići

### C.1 Zašto podizanje konstante nije bilo rješenje

`statement_timeout = 5 s` i `DEFAULT_UPDATE_TIMEOUT = 5.0` bile su **dvije nevezane
petice**. Jednakost je jamčila da svaki upit koji potroši sandbox timeout prekorači i
UPDATE prozor. Podizanje prozora pomiče prag; nesklad ostaje moguć.

### C.2 Dva dijela, nijedan sam dovoljan

**1. Prozor se izvodi iz granice, ne postavlja.**

```python
DEFAULT_UPDATE_TIMEOUT = DEFAULT_STATEMENT_TIMEOUT_S + UPDATE_TIMEOUT_MARGIN_S  # 5 + 2
```

Granica je zato dobila ime u `sandbox_runner.py` — veza se sada **vidi** umjesto da se
duplicira. 🔴 Produljenje je postalo sigurno **tek nakon #62**: stari komentar je kratak
prozor opravdavao time da „UPDATE hang blokira SVE studente", što je vrijedilo dok je FSM
bio jedan.

**2. Kad prozor ipak istekne, Coordinator provjeri je li upisano.**

- redak postoji → odgovara **stvarnim ishodom** (200, pravi feedback, `recommend_skipped`),
- ne postoji → `evaluation_timeout` je **istinit**.

Polazna crta je `max(attempts.id)` uzeta na prijemu, **ne vrijeme**: usporedba po
`created_at` mjerila bi aplikacijski sat protiv sata baze, a promašaj bi vratio točno
onaj nesklad koji popravljamo. `_settle` ponavlja provjeru kroz 2 s, jer bi redak nastao
milisekundu nakon jedne provjere dao isti nesklad — samo rjeđe.

Najgori put: UPDATE 7 + RECOMMEND 5 = **12 s < `GATEWAY_TIMEOUT` 15**.

### C.3 Izmjereno, produkcijske konstante

| upit | prije | poslije |
|---|---|---|
| `pg_sleep(4.9)`, **točan** | 504 `evaluation_timeout` **+ 1 pokušaj + 2 BKT + 30 XP** | **200**, `is_correct=true`, 30 XP |
| `pg_sleep(5.2)`, prespor | 504 `evaluation_timeout` **+ 1 pokušaj + 2 BKT** | **200**, `error_type=timeout` |

🔴 Slučaj s **točnim** sporim upitom KORAK 0 je izveo iz koda, ne izmjerio. Sada je
izmjeren: student je dobio „sustav ne odgovara" **i 30 XP**. Sada dobiva svoj rezultat.

### C.4 Što NIJE dirano

`persistence.py`, `evaluate-query` payload, migracije. D6 garancija (commit prije informa)
ostaje netaknuta.

---

## D — Mjerenja

### D.1 p95 — svaka brojka nosi broj korisnika

| mjerenje | korisnika | p50 | **p95** | max | gubitak |
|---|---|---|---|---|---|
| **stari kod** (kontrola, ista sesija) | 1 | 112,7 ms | **123,6 ms** | 130,9 | 0 |
| novi kod | 1 | 114,2 ms | **124,2 ms** | 134,3 | 0 |
| novi kod, back-to-back | 8 | 537,4 ms | **7177,9 ms** | 7336,5 | **0** |
| **novi kod, tempo evala** (predaja ~19 s) | **20** | 126,8 ms | **197,2 ms** | 7104,3 | **0** |

🔴 **Kontrola je mjerena u istoj sesiji**, vraćanjem starog koda u stablo i restartom —
ne uspoređuje se s brojkom iz 5.1 (137,3 ms), koja je s drugog dana i druge grane.
Razlika novi–stari pri K=1 je **+0,6 ms p95**, unutar devijacije (~5,5 ms): popravak ne
usporava jednog korisnika.

**Stari kod pri K=8 nije mjerljiv na ovoj skali** — davao je 1 uspjeh po rafalu
(KORAK 0 §A.2.2), pa p95 uspjelih nije bio mjera sustava nego mjera preživjelih.

### D.2 Što znači 7,2 s pri K=8

To je **najgori slučaj bez ijedne stanke za razmišljanje**: 8 studenata predaje
neprekidno. Nije scenarij evala. Red se formira na Evaluatoru (jedan `CyclicBehaviour`)
i Recommenderu (`prolog_lock`) — i **prazni se**: 40/40 zahtjeva uspjelo.

Eval-relevantna brojka je red niže: **20 studenata, p95 = 197 ms, 60/60 uspjeha**.
Od 60 predaja, 59 je dobilo pravu preporuku; jedna je dobila `recommend_skipped` —
mreža iz #63 se aktivirala, student je dobio svoj rezultat bez preporuke umjesto greške.

### D.3 Zapisano kao invarijante

- [„Brojka o performansama nosi broj istovremenih korisnika"](invarijante.md#brojka-nosi-konkurentnost)
- [„`--workers 1` je invarijanta, ne postavka"](invarijante.md#jedan-uvicorn-radnik)

---

## E — Testovi

| test | tvrdi | prije |
|---|---|---|
| `test_no_accepted_submission_is_ever_lost[2,4,8]` | K predaja → K redaka **i** K odgovora | 1 redak za svaki K |
| `test_cid_correlation_holds_under_concurrency` | nema cross-talka pod konkurentnošću | 1/4 odgovora |
| `test_no_flow_or_behaviour_leak_after_burst` | nakon K=8: `flow_count()==0`, behaviouri na polaznom broju | — |
| `test_flow_limit_refuses_explicitly_not_silently` | na granici 503 s razlogom, nikad 504 | — |
| `test_incorrect_slow_query_leaves_no_orphan_row[1,2,3]` | ili odgovor ili nikakav trag | 504 + redak + BKT |
| `test_correct_slow_query_never_awards_xp_behind_an_error[1,2,3]` | isto, uz XP | 504 + redak + BKT + 30 XP |

🔴 **Tvrde invarijante, ne brojke.** Nigdje se ne provjerava trajanje — test koji bi
tvrdio latenciju bio bi flaky na tuđem stroju, a ovi su binarni.

**Traže živu bazu i Prosody**, kao i svih 6 postojećih coordinator testova; novost je da
prvi put pišu u `tutor_main` **konkurentno**. Zato svaka nit ima vlastitog korisnika —
`uq_attempts_user_task_number` bi inače rušio test iz krivog razloga.

**Suite: 504 prolazi, 1 preskočen.** Postojećih 6 coordinator testova nedirnuto i zeleno.

---

## F — Što ostaje otvoreno

| # | stavka | zašto nije ovdje |
|---|---|---|
| 1 | `GATEWAY_TIMEOUT` prozor (15 s) i dalje može proizvesti nesklad ako tok prijeđe i njega | uklonio bi ga samo poništavanje upisa, što ruši D6 |
| 2 | tekst `submitSlot === "gateway"` | Faza 5.2; sada treba razlikovati **tri** ishoda, ne dva (v. niže) |
| 3 | N-21 — `submitted_query` u `agent_messages_log` | zamrznuti `base.py` |
| 4 | Recommender kao usko grlo pri K=8 | `prolog_lock` je svjesna odluka; ne gubi, samo čeka |

### F.1 Za 5.2 — sada su TRI ishoda, ne dva

| stanje | HTTP | `detail` | što student treba znati |
|---|---|---|---|
| tok nije ni primljen | 503 | `coordinator_busy` | „sustav je zauzet, pokušaj odmah ponovno" |
| evaluacija nije stigla, **ništa nije upisano** | 504 | `evaluation_timeout` | „nije zabilježeno, predaj ponovno" |
| gateway odustao | 504 | `orchestration_timeout` | isto kao gore |

🔴 Slučaj „upisano je, ali odgovor kasni" **više ne postoji** — takav zahtjev sada vraća
200 sa stvarnim ishodom. To je jedan UI put manje nego što je KORAK 0 predviđao.
