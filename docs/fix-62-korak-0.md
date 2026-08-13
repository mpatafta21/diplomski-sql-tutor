# #62 Korak 0 — istovremene predaje se gube (istraga, nula izmjena koda)

**Datum:** 2026-08-12 · **Grana:** `fix-coordinator-concurrency` (s čistog `main`a, `34b0e64`)
**Mjereno na `main` kodu** — bez HintAgenta u procesu, `USE_LLM_HINTS` ne postoji na ovoj grani.

---

# A — Gateway put radi ono što Coordinator ne radi

## A.1 Mehanizam korelacije u gatewayu, u cijelosti

Tri komponente, svaka s jednom zadaćom.

**1. Registry** — [`AgentBridge`](../backend/app/bridge/agent_bridge.py): `dict[correlation_id → asyncio.Future]`.

```python
def register(self) -> tuple[str, asyncio.Future]:
    correlation_id = str(uuid.uuid4())
    future = asyncio.get_running_loop().create_future()
    self._pending[correlation_id] = future
    return correlation_id, future
```

`resolve(cid, result)` traži Future po cid-u i postavlja rezultat; vraća `False` ako cid ne
postoji ili je Future već gotov — **ne baca**. `wait(cid, timeout)` čeka, i u `finally`
**bezuvjetno** briše cid iz `_pending` (LEAK GUARD).

**2. Slanje** — [`GatewayAgent.send_fipa`](../backend/app/bridge/gateway_agent.py): zakazuje
`OneShotBehaviour` koji šalje poruku s `correlation_id` u metapodacima. Pošiljatelj je
gateway JID, pa odgovor dolazi natrag na gateway.

**3. Rezolucija** — `GatewayAgent._Resolve`, `CyclicBehaviour`:

```python
msg = await self.receive(timeout=10)
cid = msg.get_metadata("correlation_id")
resolved = self.agent._bridge.resolve(cid, payload)
if not resolved:
    _log.debug("nije rezolviran cid=%s (nepoznat/already-done)")   # benigno
```

🔴 **Ključno: `_Resolve` NE ČEKA određeni cid.** Prihvati **bilo koju** poruku koja odgovara
predlošku, pročita joj cid, i potraži ga u registryju. Poruka za koju cid ne postoji ne
ruši ništa i ne blokira iduću.

## A.2 Strukturna razlika — imenovana

| | GatewayAgent | CoordinatorAgent |
|---|---|---|
| oblik | **dispatcher** (router po cid-u) | **stroj stanja s jednim utorom** |
| stanje | `dict[cid → Future]`, **N istovremenih** | `self.agent._flow`, **jedan jedini** |
| čekanje | ne čeka ništa određeno; poslužuje što stigne | `_recv_matching(cid=self.cid)` — čeka **točno jednu** poruku |
| tuđa poruka | potraži se u registryju; ako je nema, **debug i dalje** | **odbaci se, zauvijek** |

Razlika nije u brzini ni u serijalizaciji — **oba** su serijalizirana (Recommender ima
`prolog_lock`, Coordinator ima jedan mailbox). Razlika je u tome **što se radi s porukom
koja nije ona koju trenutno čekaš**: gateway je usmjeri, Coordinator je baci.

I dublje: čak i kad poruka ne bi bila bačena, Coordinator **nema gdje** držati drugi tok —
`self.agent._flow` je jedan atribut, ne registry. Popravak koji samo prestane odbacivati
poruke ne bi bio dovoljan.

## A.3 Mjerenje — `/next-task` ne gubi ništa

Isti harness kao za `/attempt`: K niti, svaka svoj korisnik, `threading.Barrier`, točno
jedan zahtjev po niti.

| K istovremenih | rafala | zahtjeva | **uspjelo** | uspjeha/rafalu | neuspjeha |
|---|---|---|---|---|---|
| 2 | 3 | 6 | 6 | **2,0** | 0 |
| 4 | 3 | 12 | 12 | **4,0** | 0 |
| 8 | 3 | 24 | 24 | **8,0** | 0 |

**Nijedan zahtjev nije izgubljen ni na jednoj razini.** Usporedno, `/attempt` daje 1,0
uspjeha po rafalu na svakom K.

Latencije pri K=8 (ms): `87, 93, 105, 116, 125, 132, 141, 147, 159, 172, 177, 186, 205,
205, 218, 233, 236, 247, 260, 266, 272, 289, 291, 291`.

🔴 Ta **stepenica** je dokaz da se red čekanja formira i **prazni**. Recommender je
serijaliziran (`prolog_lock`), pa zahtjevi čekaju — ali svaki dođe na red. Točno to
`/attempt` ne radi: ondje uspjeli ostaju na ~120 ms **na svakoj razini**, jer višak nikad
ne uđe u red.

**Presuda #62 se NE širi.** Kvar je lokaliziran u `CoordinatorAgent`.

## A.4 Popravak je primjena postojećeg obrasca — s jednim novim dijelom

**Postoji:** registry `cid → stanje` + dispatcher koji usmjerava po cid-u. `AgentBridge` je
to već, radi u produkciji od 3E.3, i **ima vlastite testove**
([`test_agent_bridge.py`](../backend/tests/test_agent_bridge.py), 12 testova nad LEAK GUARDom).

**Nedostaje:** Coordinatorov tok nije jedan Future nego **višekoračni stroj stanja**
(RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND). Registry mora držati *stanje toka*, a
ne samo Future, i netko mora **voziti** svaki tok neovisno.

Dakle: **korelacijski dio je prepisivanje postojećeg obrasca, orkestracijski dio je nov.**
To određuje opseg — nije istraživački zadatak, ali nije ni troredna zakrpa.

---

# B — Što se točno gubi i gdje

## B.1 Put odbačene poruke

| # | mjesto | što se dogodi |
|---|---|---|
| 1 | [`routes.py:203`](../backend/app/api/routes.py#L203) | `bridge.register()` → `(cid, future)`, cid u `_pending` |
| 2 | [`routes.py:205`](../backend/app/api/routes.py#L205) | `gateway.send_fipa(...)` → `submit-attempt` Coordinatoru |
| 3 | `gateway_agent._Send` | poruka poslana, **i zabilježena** u `agent_messages_log` |
| 4 | [`coordinator.py:196-209`](../backend/agents/coordinator.py#L196-L209) | FSM je u UPDATE/RECOMMEND, čeka svoj cid; ova poruka ne matcha → **`_log.debug` i petlja dalje**. Poruka je potrošena iz mailboxa i **nestala** |
| 5 | [`routes.py:213`](../backend/app/api/routes.py#L213) | `bridge.wait` istekne nakon `GATEWAY_TIMEOUT=15` |
| 6 | [`routes.py:216`](../backend/app/api/routes.py#L216) | HTTP **504 `orchestration_timeout`** |

Student vidi „Sustav ne odgovara". Ništa drugo se nije dogodilo.

## B.2 Trag postoji — gubitak NIJE potpuno tih

🔴 **Ispravak moje ranije formulacije.** U wrapupu 5.1 napisao sam da rad „nestaje bez
zapisa igdje osim u `agent_messages_log`". Prva polovica je točna (nema retka u `attempts`),
ali druga je važnija nego što sam je prikazao: `agent_messages_log` daje **potpunu i
pretraživu signaturu** izgubljene predaje.

Mehanizam: svaku poruku bilježe **oba** agenta — pošiljatelj nakon slanja, primatelj pri
primitku. Odbačena poruka nikad ne dođe do primateljevog `log_message`, pa ima **samo
pošiljateljev redak**.

Forenzika nad cijelom bazom (874 tokova, od 2026-07-20):

| skupina | kriterij | broj | redaka u `attempts` |
|---|---|---|---|
| — | `submit-attempt` ukupno | 874 | — |
| — | s odgovorom Coordinatora | 647 | — |
| **A** | bez odgovora, **nikad do Evaluatora** → odbačeno u RECEIVE | **99** | **0** |
| **B** | bez odgovora, do Evaluatora ali evaluacija nedovršena | **128** | **0** |
| **C** | bez odgovora, **evaluacija dovršena** | **0** | — |

Skupina A je datirana isključivo **2026-08-12** — moja današnja mjerenja. Skupina B je
raspoređena (07-25: 8, 07-26: 8, 08-11: 72, 08-12: 40) i ne nosi potpis #62: to su tokovi
prekinuti nasred evaluacije, gotovo sigurno gašenjem procesa tijekom razvoja. **Ne
pripisujem ih #62** — nemam kontrolu koja bi to potvrdila.

🔴 **Praktična posljedica:** postoji izvediv upit koji broji izgubljene predaje
retroaktivno. Za eval to znači da se gubitak može **mjeriti**, ne samo pretpostavljati.

## B.3 Što još ide kroz Coordinator — samo `/attempt`

[`_coordinator_template()`](../backend/agents/coordinator.py#L410-L418) propušta tri
ontologije, ali samo jedna **pokreće** tok:

| ontologija | uloga | pokreće tok? |
|---|---|---|
| `submit-attempt` | ulaz iz gatewaya (`POST /attempt`) | **da** |
| `model-updated` | odgovor KM-a *unutar* toka | ne |
| `recommend-next` | odgovor Recommendera *unutar* toka | ne |

Ostale rute Coordinator ne dodiruju: `/next-task` ide izravno Recommenderu, `/run` i
`/profile` uopće ne koriste agente. **Izloženo je točno jedno korisničko djelovanje —
predaja rješenja.** To je ujedno jedino djelovanje koje nosi ocjenu, XP i BKT.

## B.4 🔴 STANI I JAVI — DA, scenarij „redak nastane, student vidi grešku" postoji

Odgovor je **potvrdan**, i gori je nego što pitanje pretpostavlja: **ne treba nikakav pad
procesa.**

### Put kroz kod

`UpdateState` čeka `model-updated` do `DEFAULT_UPDATE_TIMEOUT = 5.0`
([coordinator.py:77](../backend/agents/coordinator.py#L77)). Na istek:
`flow["error"] = ERROR_EVALUATION_TIMEOUT` → RESPOND → HTTP **504**.

Ali Evaluator je u međuvremenu **već commitao** — to je D6 garancija
([evaluator_agent.py:7-8](../backend/agents/evaluator_agent.py#L7-L8)), commit **prije**
informa — i GamificationAgent se pokreće na Evaluatorov inform, **neovisno o Coordinatoru**.
Coordinatorov timeout ne zaustavlja ništa nizvodno.

### Reproducirano, 3/3

`POST /attempt` sa `SELECT pg_sleep(6);` (sandbox `statement_timeout = 5 s`):

| pokušaj | HTTP | trajanje | redaka u `attempts` | BKT snapshotova |
|---|---|---|---|---|
| 1 | 504 `evaluation_timeout` | 5076 ms | **1** | **2** |
| 2 | 504 `evaluation_timeout` | 6620 ms | **1** | **2** |
| 3 | 504 `evaluation_timeout` | 5115 ms | **1** | **2** |

FIPA trag jednog takvog toka (isti `cid` kroz cijeli lanac):

```
13:56:47.773  coordinator  -> evaluator     request
13:56:52.813  evaluator    -> knowledge     inform     ← +5,04 s, evaluacija gotova
13:56:52.818  evaluator    -> gamification  inform
13:56:52.824  coordinator  -> gateway       inform     ← evaluation_timeout (504)
13:56:52.860  knowledge    -> coordinator   inform     ← stiže NAKON što je odustao
```

**Student je dobio „sustav ne odgovara". U bazi: pokušaj zabilježen, BKT ažuriran,
Gamification obaviješten.**

### Zašto ovo nije rubni slučaj

Sandbox `statement_timeout` je **5 s**, a `DEFAULT_UPDATE_TIMEOUT` je **5,0 s**. Svaki upit
koji potroši statement timeout nužno prekorači i UPDATE prozor — režijski trošak uvijek
doda nekoliko ms. To znači: **svaki student čiji upit padne na sandbox timeoutu** (nedostaje
uvjet spajanja → kartezijev produkt; to je uobičajena greška u učenju SQL-a) dobiva 504 dok
mu se pokušaj tiho bilježi i BKT kažnjava.

Student zatim ponovno preda — i bude kažnjen **dvaput za isti upit**.

🔴 **Izmjereno je `xp_awarded = 0`, jer je pokušaj bio netočan.** Da isti prekoračeni prozor
zadesi **točan** upit, XP bi bio dodijeljen dok student vidi grešku. Taj slučaj **nisam
izmjerio** — trebao bi točan upit sporiji od 5 s, a točnost se provjerava usporedbom s
`expected_result`, pa ga nije trivijalno konstruirati. Iz koda slijedi da bi se dogodio
(Gamification visi o Evaluatorovom informu, ne o Coordinatoru), ali to je **izvod, ne
mjerenje**, i tako ga treba čitati.

**Ovo je zaseban kvar od #62** — druga uzročna veza, isti simptom. Ne popravlja ga isti
zahvat: #62 traži korelacijski router, ovaj traži da se timeout i perzistencija slože
(ili da se odgovor pošalje kasno, ili da se pokušaj ne bilježi dok tok nije zaključen).

---

# C — Smjerovi popravka

## C.1 Future/correlation obrazac iz gatewaya na Coordinator

**Opseg:** `_flow` postaje `dict[cid → flow]`; `_recv_matching` prestaje čekati određeni cid
i postaje dispatcher; svako stanje FSM-a mora primati cid kao argument umjesto da ga čita
iz `self.agent._flow`.

**Rizik:** srednji-visok. Dira **svako** stanje FSM-a, dakle cijeli eval-verificirani put.

**Dokazivo testom:** da — test iz §D pada danas, prolazi poslije.

## C.2 Tuđa poruka se VRAĆA u red umjesto da se odbaci

**Opseg:** najmanji — samo `_recv_matching`. SPADE `Behaviour` nema `unreceive`, pa bi
trebao vlastiti međuspremnik: skupi ne-matchane poruke, vrati ih u mailbox nakon što tok
završi.

**Rizik:** 🔴 **zavaravajuće nizak.** Riješio bi *odbacivanje*, ali ne i **jedan utor**:
zahtjevi bi se serijalizirali, svaki bi čekao ~130 ms × pozicija u redu. Uz `GATEWAY_TIMEOUT
= 15 s` to podnosi ~115 zahtjeva u redu, što je za 20 sudionika dovoljno. **Ali** jedan spor
tok (5 s sandbox timeout) blokira sve iza sebe, pa se red uz nekoliko sporih upita pretvara
u val 504-ica.

**Dokazivo testom:** da, istim testom.

## C.3 Instanca FSM-a po razgovoru

**Opseg:** velik — životni ciklus behavioura, čišćenje, granica broja istovremenih tokova.

**Rizik:** visok. Nizvodni agenti nisu pisani za paralelizam: Recommender ima `prolog_lock`
(pa bi ionako serijalizirao), Evaluator otvara sandbox konekciju po pozivu. Otvara pitanja
koja danas ne postoje.

**Dokazivo testom:** da, ali traži i test iscrpljenja resursa.

## C.4 `/attempt` zaobilazi Coordinator kao `/next-task`

**Opseg:** ruta preuzima orkestraciju; Coordinator ostaje bez potrošača.

🔴 **Što se gubi u tvrdnji rada.** Ovo nije tehnički kompromis nego **izmjena doprinosa**.
Rad tvrdi *višeagentski sustav s orkestracijom*; CoordinatorAgent i njegov FSM su
materijalni dokaz te tvrdnje — jedino mjesto gdje agent koordinira druge agente umjesto da
odgovara na zahtjev. Bez njega ostaje pet agenata koje poziva HTTP sloj, što je **servisna
arhitektura s FIPA porukama**, ne agentska orkestracija. Poglavlje o arhitekturi bi se
moralo prepisati, a obrana bi morala braniti da je „koordinator" bio suvišan — što bi bilo
priznanje da ga sustav nije trebao.

**Ne preporučujem**, i to ne zbog opsega nego zbog toga.

## C.5 🔴 Preporuka: C.1 (dispatcher), s C.2 kao mostom

**Preporučujem C.1.**

1. **Pravi uzrok, ne simptom.** Invarijant iz `coordinator.py:29-31` postaje **istinit**
   umjesto da ga se zaobilazi. Komentar već predviđa upravo taj zahvat: „guard mora postati
   pravi correlation-router".
2. **Obrazac postoji i dokazan je u produkciji.** `AgentBridge` radi isti posao od 3E.3 i
   ima vlastite testove. Ne izmišlja se mehanizam.
3. **Čuva doprinos rada.** Coordinator ostaje orkestrator; postaje orkestrator koji podnosi
   više od jednog studenta. To je **jača** tvrdnja za rad, ne slabija — i poglavlje o
   konkurentnosti dobiva izmjereno prije/poslije umjesto ograde.
4. **C.2 kao most:** ako pred rokom zatreba, C.2 je manji zahvat koji uklanja *gubitak*
   (najgori dio) i ostavlja *čekanje*. Nije rješenje, ali je isporučiv međukorak — pod
   uvjetom da se zapiše da spori upit i dalje blokira red.

Za oba vrijedi: **prvo test iz §D, pa popravak.** Test mora pasti na današnjem kodu prije
nego se dirne išta.

---

# D — Test koji bi ovo uhvatio

## D.1 Zašto ga 737 testova nema

Postoji `test_cid_correlation_two_sequential_flows`
([test_coordinator.py:444](../backend/tests/test_coordinator.py#L444)). Njegov docstring:

> „Sekvencijalno jer FSMBehaviour serijalizira (GATE 2, svjesna MVP odluka)."

🔴 Test **ugrađuje ograničenje u svoj dizajn** umjesto da ga propituje. Postoji i
`test_stale_message_guard_drops_foreign_cid` — ali on šalje stranu **`model-updated`**
(mrtvu poruku, slučaj koji invarijant pokriva), nikad strani **`submit-attempt`** (budući
zahtjev, slučaj u kojem invarijant pada). Guard je testiran točno ondje gdje je ispravan.

To je peti primjerak obrasca iz **NALAZA #57**: test pisan prema promatranom ponašanju
zaključava kvar kao specifikaciju.

## D.2 Skica testa (nije izveden)

```python
# tests/test_coordinator_concurrency.py
@pytest.mark.asyncio
async def test_no_accepted_submission_is_ever_lost(coord_env):
    """🔴 INVARIJANTA: nijedna prihvaćena predaja se ne gubi.

    Ne mjeri latenciju, ne mjeri p95, ne tvrdi koliko je brzo. Tvrdi da broj
    redaka u `attempts` naraste za točno onoliko koliko je predaja prihvaćeno.

    PADA na današnjem kodu: K=4 daje 1 redak.
    """
    K = 4
    prije = broj_redaka_attempts(users)

    # K istovremenih submit-attempt poruka, RAZLIČITI korisnici i cid-evi
    await asyncio.gather(*[posalji_submit(user_id=u, cid=uuid4()) for u in users])
    await _poll(lambda: broj_redaka_attempts(users) - prije == K, timeout=30)

    assert broj_redaka_attempts(users) - prije == K, (
        "prihvaćena predaja je izgubljena — poruka odbačena u drain-loopu"
    )
    # Druga polovica invarijante: svaka predaja je i ODGOVORENA.
    assert {r["correlation_id"] for r in probe.responses} == set(cids)
```

## D.3 Tvrdi invarijantu, ne broj

Test **ne** provjerava p95, prosjek ni trajanje. Provjerava dvije stvari:

1. `count(attempts)` poraste za točno K — **ništa prihvaćeno nije izgubljeno**,
2. skup `correlation_id`-eva u odgovorima jednak je skupu poslanih — **svatko je dobio svoj
   odgovor**.

Obje su binarne i vrijede neovisno o stroju, opterećenju i brzini. Zato ne mogu postati
flaky kao mjerenje latencije.

## D.4 Gdje živi i treba li živu bazu

**pytest**, uz postojeći `coord_env` obrazac iz `test_coordinator.py`: pravi
`CoordinatorAgent` + mock Evaluator/Knowledge/Recommender + `_GatewayProbe`.

**Treba živu bazu i Prosody** — kao i svih 6 postojećih coordinator testova. Bez XMPP-a nema
mailboxa, a upravo je mailbox predmet testa. E2E (Playwright) nije prikladan: `workers: 1,
fullyParallel: false`, i ne bi vidio redak u bazi.

Alternativa bez baze: test nad samim `_recv_matching` koji tvrdi da ne-matchana poruka
**nije izgubljena**. Brz i determinističan, ali dokazuje manje — ne pokriva `_flow` kao
jedan utor (§A.2).

## D.5 🔴 STANI I JAVI — invarijante koje nijedan test ne izvršava

Pregledao sam sve tvrdnje u `agents/` i `app/bridge/`. Popis je **kratak**, i to je nalaz za
sebe: suite je dobar, a rupa je točno na nosivom mjestu.

| # | invarijanta | gdje | test | stanje |
|---|---|---|---|---|
| 1 | „svaka ne-self.cid poruka je nužno MRTVA … drop je siguran" | `coordinator.py:29-31` | **nijedan** | 🔴 **OPOVRGNUTA** danas |
| 2 | GATE 2: posljedica globalne serijalizacije pod konkurentnim klijentima | `coordinator.py:20-25` | **nijedan** (postojeći je namjerno sekvencijalan) | 🔴 neizvršena |
| 3 | „timeout je UKUPNI (deadline), NE resetira se po odbačenoj poruci" | `coordinator.py:187-188` | **nijedan** (stale test šalje jednu poruku) | 🟡 neizvršena |
| 4 | „novi `SessionLocal()` po `run()`; nikad se ne dijeli kroz pozive" | `evaluator_agent.py:10-12` | **nijedan** | 🟡 neizvršena, strukturna |

**Izvršene su** (kontrast koji pokazuje da je ovo rješiv problem, ne stanje stvari):

| invarijanta | gdje | test |
|---|---|---|
| LEAK GUARD: `pending_count == 0` na svakom ishodu | `agent_bridge.py:47` | `test_agent_bridge.py`, 12 testova |
| plain-bridge: isti event loop | `agent_bridge.py:17-34` | `test_api.py::test_same_loop_bridge_resolves` |
| D6: commit prije informa | `evaluator_agent.py:7-8` | `test_evaluator_agent.py:260-262` |
| `prolog_lock` serijalizira Prolog VM | `recommender_agent.py:6-11` | `test_recommender_agent.py::test_concurrent_recommends_serialized_and_correct` |
| „uvijek odgovori informom, i na grešci" | `recommender_agent.py:21-22` | `test_recommender_agent.py:307` |

🔴 **Obrazac koji ide u rad.** Četiri neizvršene invarijante nisu nasumične — **sve četiri
opisuju ponašanje pod uvjetima koje nijedan test ne stvara** (konkurentnost, poplava
zastarjelih poruka, dijeljenje sesije). Izvršene invarijante opisuju ponašanje **jednog
poziva**. Suite dokazuje što sustav radi kad ga se pita jedanput, a invarijante u
komentarima tvrde što radi kad ga se pita više puta odjednom — i baš te tvrdnje nitko nije
provjerio. Jedna od njih je bila neistinita **od Faze 3E.3**, tri mjeseca.

---

# E — Posljedice za već izmjereno

## E.1 🔴 Da — sva ranija mjerenja tiho su pretpostavljala nepreklapanje

Provjereno, ne pretpostavljeno:

| mjerenje | konkurentnost | ovisi o nepreklapanju? |
|---|---|---|
| p95 `/attempt` iz 5.1 (137,3 / 135,2 / 134,1 ms) | jedan sekvencijalni klijent | **da** |
| p95 „pod 3 paralelna hinta" (5.1) | 3 hinta + 1 `/attempt` niz | **ne** — hint ne ide kroz FSM (§B.3) |
| `make sweep` / preflight | zove `agents.evaluation.evaluate` izravno | ne dodiruje lanac |
| `pilot_run.py` | `for` petlje, sekvencijalno | **da** |
| Playwright e2e | `workers: 1`, `fullyParallel: false` | **da** |
| `test_coordinator.py` (6 testova) | sekvencijalno po dizajnu | **da** |

**Nijedna brojka nije neistinita.** Sve su uže nego što se čine: opisuju sustav **s jednim
korisnikom**. Nijedan izmjereni broj ne opisuje ponašanje s dvoje.

To vrijedi i za p95 iz 5.1: tvrdnja „HintAgent ne mijenja p95" i dalje stoji, jer je hint
put nezavisan — ali „p95 = 134 ms" opisuje **prazan sustav**, i tako se mora citirati u radu.

## E.2 Tekst za `submitSlot === "gateway"` — prijedlog, ne primjena

Današnji: *„Sustav ne odgovara — Evaluacija je predugo trajala — pokušaj ponovno predati."*

Netočan je **dvaput**: evaluacija nije trajala (poruka je odbačena prije evaluacije), a
implicira da je predaja negdje zapisana.

Problem: ista 504 grana pokriva **dva različita ishoda** koje UI danas ne razlikuje:

| `detail` | što se stvarno dogodilo | što student treba znati |
|---|---|---|
| `orchestration_timeout` | predaja **odbačena**, ništa nije zabilježeno | „nije zabilježeno, predaj ponovno" |
| `evaluation_timeout` | predaja **zabilježena**, upit je bio prespor (§B.4) | „upit je predugo trajao, zabilježen je kao neuspješan" |

Prijedlog (**ne primjenjujem** — ovisi o ishodu popravka; ako C.1 prođe, prva grana
prestaje postojati):

- `orchestration_timeout` → **„Predaja nije zabilježena.** Sustav je bio zauzet drugom
  predajom. Pokušaj ponovno — ništa nije izgubljeno osim ovog pokušaja."
- `evaluation_timeout` → **„Upit je predugo trajao** i prekinut je nakon 5 sekundi. Pokušaj
  je zabilježen kao neuspješan. Provjeri nedostaje li uvjet spajanja."

## E.3 Deployment — horizontalno skaliranje NE pomaže

Danas: **jedan** uvicorn proces, bez `--workers`
([Makefile:168](../Makefile#L168), `--reload` u devu). Jedan proces → jedan SPADE Container
→ **jedna** instanca svakog agenta, uključujući Coordinator.

🔴 **Dodavanje uvicorn radnika ne bi pomoglo, nego bi odmoglo.** Svaki radnik pokreće
vlastiti `start_gateway_stack` i prijavio bi se na Prosody **istim JID-om**
(`coordinator@localhost` iz `.env`). Dvije sesije istog bare JID-a znače da isporuka ovisi o
prioritetu resursa — poruke bi odlazile jednoj od instanci nepredvidivo, a `AgentBridge` je
**in-process dict**: Future čeka u radniku A, odgovor može stići radniku B i ondje se tiho
izgubiti (`resolve` vraća `False`, `_log.debug`). Ista klasa gubitka, teža za dijagnozu.

Za više radnika trebalo bi: JID po radniku, i registry izvan procesa (Redis ili sl.). To je
druga arhitektura, ne postavka.

**Zaključak: jedan Coordinator je usko grlo neovisno o skaliranju** — dok se ne popravi
§C.1. Nakon popravka usko grlo postaje nizvodni `prolog_lock` u Recommenderu, koji **ima
red** i ne gubi (dokazano u §A.3).

---

# F — Entry / exit za popravak

**Entry:**
1. Odabran smjer (preporuka: §C.1).
2. Test iz §D **napisan i dokazano crven** na `main` kodu — prije ijedne izmjene
   `coordinator.py`.
3. Odluka o §B.4 (zaseban kvar) — ide li u isti zahvat ili u vlastiti.

**Exit (mjerivo):**

1. Test iz §D zelen: K = 2, 4, 8 istovremenih predaja → K redaka u `attempts`, K odgovora s
   ispravnim `correlation_id`-em.
2. Rafal-harness (`burst_attempt.py`) daje **K uspjeha po rafalu**, ne 1.
3. `bench_concurrency.py` na razinama 1–8: **0 × 504**, i latencija uspjelih raste
   stepenasto (kao `/next-task` danas), što dokazuje red umjesto gubitka.
4. Forenzički upit iz §B.2 nad razdobljem testa: **0 tokova bez odgovora**.
5. Postojećih 6 coordinator testova i dalje zeleno; puna suite bez regresije.
6. p95 jednog sekvencijalnog klijenta **nepromijenjen** naspram 137,3 ms baselinea — popravak
   ne smije usporiti prazan sustav.
7. Invarijanta u `coordinator.py:29-31` **prepisana** da opisuje novo ponašanje, sa sidrom u
   `docs/invarijante.md` i citatom testa koji je izvršava.

**Izvan opsega:** §B.4 (ako se odluči zasebno), N-21 (`submitted_query` u FIPA logu),
UI tekstovi iz §E.2.
