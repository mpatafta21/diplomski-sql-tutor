# Faza 5, KORAK 0 — HintAgent: istraga prije gradnje

**Grana:** `faza-5-hintagent`, s čistog `main`a nakon mergea PR-a #26
**Datum:** 2026-08-11
**Opseg:** read-only. Nula izmjena u `backend/`, `frontend/src/`, `schema.d.ts`.
Jedina izmjena u repou je **ovaj dokument**.

---

## A — GIT GATE

### A.1 Je li se `main` pomaknuo? ❌ NIJE

```
$ git rev-parse HEAD origin/main
34b0e64150ed148e5fdc918a3fb1984105e74464
34b0e64150ed148e5fdc918a3fb1984105e74464
```

Lokalni `main` i `origin/main` pokazuju na **isti commit** — merge commit `34b0e64`
(„Merge pull request #26 from mpatafta21/faza-4-7-polish"). Grana `faza-5-hintagent`
odvojena je točno odatle.

### A.2 Je li ijedan artefakt ušao a ne pripada? ❌ NIJE

```
$ git status --porcelain
(prazno)
```

Radno stablo čisto, nula untracked datoteka. Ništa iz 4.7 nije procurilo.

> **Napomena o privremenim artefaktima ove istrage.** Za mjerenje u §B.6 korišten je
> harness (`_diag_hint_row.html`, `_diag_measure*.mjs`) postavljen u `frontend/dist/`
> — direktorij je u `.gitignore` (`git check-ignore dist` prolazi) i regenerira se
> `npm run build`om. **Obrisani su nakon mjerenja**; `git status` gore je snimljen
> nakon brisanja. Nijedna praćena ni untracked datoteka nije prepisana.

---

## B.1 🔴 PRIVATNOST — hint šalje studentov SQL trećoj strani

### B.1.1 Točan tekst iz `participation.ts`

Dva odlomka su relevantna
([participation.ts:41](frontend/src/lib/participation.ts#L41),
[participation.ts:47](frontend/src/lib/participation.ts#L47)):

```ts
"Dok rješavaš zadatke, sustav bilježi tvoje SQL upite, ishode pokušaja i procjenu znanja po konceptu, vezano uz tvoj račun.",
```

```ts
"Podaci se čuvaju do obrane rada, nakon čega se brišu. U radu ostaje samo pseudonimizirani skup podataka bez korisničkih imena i e-adresa.",
```

Uz to, komentar u zaglavlju datoteke izričito nabraja što se **namjerno ne tvrdi**
([participation.ts:14-21](frontend/src/lib/participation.ts#L14-L21)):

```ts
/**
 * 🔴 NAMJERNO NIJE OVDJE (i ne smije se dodati bez odluke):
 *  - rok čuvanja podataka — nije određen, izmišljanje bi bila neistina
 *  - pozivanje na konkretne članke GDPR-a — nemam osnovu za takvu tvrdnju
 *  - tvrdnja o anonimnosti — username i e-adresa SE spremaju, pa bi „anonimno"
 *    bilo netočno. Pseudonimizacija se odnosi na PRIKAZ u radu, ne na pohranu.
 *  - checkbox suglasnosti — bilježena suglasnost traži novu kolonu, dakle
 *    backend izmjenu; backend je zamrznut (🔒 errata) → Faza 5, ne 4.7.
 */
```

**Presuda:** glagol je **`bilježi`** — jednosmjerna radnja unutar sustava. Sudionik
iz tog teksta može razumno zaključiti da upit ostaje u sustavu koji mu je opisan
(FOI diplomski rad). **Ni jedna riječ ne kaže da upit napušta sustav prema trećoj
strani.** Čim HintAgent proslijedi `submitted_query` LLM-u, tekst postaje neistinit
**po propustu** — točno isti razred kao #46 (obećanje o brisanju koje nije dokazano
izvedivo).

Pogoršavajuća okolnost, ista kao kod #46: od 4.7-1a-dopune isti tekst stoji i na
**Profilu**, dakle trajno pred svakim prijavljenim korisnikom, ne jednokratno prije
registracije.

### B.1.2 Što bi TOČNO išlo prema LLM-u — minimalni skup

Popis je izveden iz onoga što HintAgent stvarno može dohvatiti u trenutku zahtjeva
(prije predaje!), po izvorima:

| polje | izvor | osobni podatak? | nužno za hint? |
|---|---|---|---|
| `submitted_query` | tijelo zahtjeva (editor, još nije predano) | 🔴 **DA** — studentov autorski tekst | ne (v. B.1.4) |
| `task.description` | `tasks.description` | ne — statički sadržaj kataloga | **da** |
| `task.difficulty` | `tasks.difficulty` | ne | pomoćno |
| `primary_concept.code` | `task_concepts` + `concepts` | ne | **da** |
| `error_type` | `EvaluationOutcome.error_type` iz **prethodnog** attempta | ne (7 vrijednosti taksonomije) | **da** |
| `detail` | `attempts.detail` prethodnog attempta | 🟡 **posredno** — sadrži imena stupaca **studentovog** upita i PG poruku ([models.py:191-192](backend/app/db/models.py#L191-L192)) | pomoćno |
| `p_L` primarnog koncepta | `skill_mastery.p_l` | ne po sebi (broj), ali je **procjena znanja osobe** | pomoćno |
| `attempt_number` | `attempts.attempt_number` | ne | pomoćno |
| `expected_query` | `tasks.expected_query` | ne, ali je **RJEŠENJE** | 🔴 **NE — nikad** |
| `expected_result` | `tasks.expected_result` | ne, ali je **RJEŠENJE** | 🔴 **NE — nikad** |
| `username` / `email` | `users` | 🔴 **DA** | **NE** |

**Minimalni skup koji je i pedagoški dostatan i privatnosno najjeftiniji:**

```
{ concept_code, task_description, difficulty, error_type, p_L_bucket, attempt_number }
```

🔴 **Dva izričita zabrana koja moraju biti kodirana, ne samo dogovorena:**

1. **`expected_query` / `expected_result` NIKAD ne idu u prompt.** Isti invarijant
   koji `TaskDetailResponse` već poštuje
   ([schemas.py:129-131](backend/app/api/schemas.py#L129-L131): *„NAMJERNO bez
   expected_query / expected_result / sandbox_schema — rješenje se NE izlaže kroz
   ovaj endpoint"*). Ako uđu u prompt, LLM će ih doslovno prepisati u hint i hint
   postaje rješenje.
2. **`username` / `email` nikad.** Trivijalno, ali mora biti u testu, ne u
   dobroj namjeri — payload se gradi iz DB reda, a `User` red nosi oboje.

### B.1.3 🔒 PRIJEDLOG DOPUNE TEKSTA — **NIJE PRIMIJENJEN, čeka odluku**

Tekst ide u rad, pa se mijenja svjesno i uz odluku (pravilo iz zaglavlja
`participation.ts`). Dvije varijante, ovisno o ishodu odluke iz §B.1.4.

**Varijanta A — hint ŠALJE upit (traži se ako se ide s punim kontekstom):**

Novi odlomak, umeće se **iza** postojećeg odlomka o bilježenju (indeks 2 u
`SUDJELOVANJE_ODLOMCI`), da redoslijed „što se bilježi → kome se šalje → kako se
prikazuje" ostane čitljiv:

> „Kad zatražiš savjet (hint), sustav šalje tvoj upit i podatke o zadatku vanjskoj
> usluzi umjetne inteligencije (Anthropic, Claude API) koja sastavlja savjet. Bez
> zahtjeva za savjetom ništa se ne šalje izvan sustava. Savjet možeš ne tražiti i
> zadatke rješavati normalno."

**Varijanta B — hint NE ŠALJE upit (v. B.1.4):**

> „Kad zatražiš savjet (hint), sustav šalje vanjskoj usluzi umjetne inteligencije
> (Anthropic, Claude API) opis zadatka, vrstu greške i procjenu tvog znanja tog
> koncepta — **ne i tekst tvog upita**. Bez zahtjeva za savjetom ništa se ne šalje
> izvan sustava."

**Zašto se imenuje usluga.** „Vanjska usluga" bez imena nije informacija — sudionik
ne može procijeniti ni jurisdikciju ni politiku čuvanja. Ime je jedini dio koji
tvrdnju čini provjerljivom.

🔴 **Ovo se ne primjenjuje u ovom koraku.** Odluka je korisnikova, i vezana je uz
odluku iz B.1.4 (koja varijanta uopće vrijedi).

### B.1.4 🔴 Može li hint raditi BEZ slanja upita? DA — i to je bitno manji zahvat

**Odgovor: da, i sustav za to već ima sve podatke.**

Ono što HintAgent treba za pedagoški koristan savjet dolazi iz **klasifikacije**,
ne iz teksta upita:

- `error_type` iz taksonomije ([evaluation.py:7-14](backend/agents/evaluation.py#L7-L14)):
  `syntax_error` · `unsupported_eval` · `execution_error` · `empty_result` ·
  `wrong_columns` · `row_mismatch` (+ `timeout`)
- `primary_concept.code` — jedan od 30 koncepata
- `p_L` iz BKT-a — gdje student stoji na tom konceptu
- `attempt_number` — koliko je puta već pokušao

To je isti signal iz kojeg `misconception_logic.py` već izvodi kod pogrešnog
razumijevanja: `"{primary_concept}__{error_type}"`
([misconception_logic.py:3-5](backend/agents/misconception_logic.py#L3-L5)).

**IZMJERENO — koliko hint time gubi.** Mjera je koliko je stanja razlučivo bez
teksta upita:

| dimenzija | broj razlučivih vrijednosti | izvor |
|---|---|---|
| `error_type` | **7** | `evaluation.py` taksonomija |
| `primary_concept` | **30** | `SELECT count(*) FROM concepts` |
| `p_L` u 3 razreda (nisko/srednje/visoko) | **3** | `skill_mastery.p_l` |
| `attempt_number` u 2 razreda (1. / ponovljeni) | **2** | `attempts.attempt_number` |

→ **1 260 razlučivih situacija** bez ijednog znaka studentovog upita, prije nego se
uzme u obzir `task.description` (koja je različita za svih **80** aktivnih zadataka).
S opisom zadatka: **do 100 800 razlučivih ulaza**.

**Što se STVARNO gubi:** hint ne može reći *„zamijenio si `INNER JOIN` s `LEFT JOIN`"*
— može reći samo *„kod ovog koncepta česta greška je krivi tip spoja; provjeri koje
retke želiš zadržati kad desna strana nema para"*. Dakle:

| gubi se | ne gubi se |
|---|---|
| upućivanje na **konkretan red** studentovog SQL-a | vezanost hinta uz **konkretnu grešku** koju je student napravio |
| „ti si napisao X, a treba Y" | „kod ove greške na ovom konceptu, provjeri Z" |
| razlikovanje dva različita upita s **istim** `error_type` na istom zadatku | razlikovanje 1 260 (odnosno do 100 800) situacija |

**Djelomično posredovanje (varijanta B+):** `attempts.detail` nosi *imena stupaca
studentovog upita* i PG poruku ([models.py:191-192](backend/app/db/models.py#L191-L192)),
što vraća dobar dio konkretnosti (`wrong_columns` postaje *„vratio si `name, price`,
a traže se 3 stupca"*) **bez slanja cijelog SQL-a**. To je ipak osobni podatak
(izveden iz studentovog teksta) i mora se imenovati u tekstu suglasnosti ako se
šalje — ali je **znatno uži** od slanja cijelog upita.

🔴 **Preporuka: varijanta B (bez upita), s `detail`om kao opcijom koja se odlučuje
zasebno.** Obrazloženje: dobitak u konkretnosti ne opravdava prelazak granice
„podaci ne napuštaju sustav", koja je jedina jednostavna i istinita rečenica koju
sudioniku možemo dati. Sustav i inače **ne evaluira upit u trenutku traženja hinta**
— hint se traži *prije* predaje, pa `error_type` dolazi iz **prethodnog** attempta;
za prvi pokušaj na zadatku hint ionako nema klasifikaciju i mora raditi samo iz
koncepta + opisa.

### B.1.5 Broj errate

🔴 **ERRATA #59** (zadnji zauzet je #58 — `docs/errata.md:748`).
Naslov prijedloga:

> **#59 🔴 Informacija sudionika ne pokriva slanje podataka vanjskoj usluzi (HintAgent)**
> Srodno: **#46** (isti razred — tvrdnja u `participation.ts` postaje neistinita po
> propustu čim se ponašanje sustava proširi), #37, #40.

Status: **otvoren — blokator za puštanje hinta u eval**, ne za gradnju iza feature
flaga (`USE_LLM_HINTS=false` znači da se ništa ne šalje, pa tekst ostaje istinit).

---

## B.2 PROVIDER — plan traži OpenAI, projekt već ima Anthropic

### B.2.1 Kako je Anthropic ključ konfiguriran i gdje se čita

**Deklariran** — [`backend/.env.example:7`](backend/.env.example#L7):

```
ANTHROPIC_API_KEY=sk-ant-api03-tvoj-pravi-kljuc-ovdje
```

**Čita se `os.environ`om, isključivo u offline skriptama:**

```
backend/scripts/generate_tasks.py:502,523
backend/scripts/meta_generate_yamls.py:363
backend/scripts/pilot_run.py:199
backend/scripts/regenerate_phantoms.py:64
backend/tests/test_generate_tasks_integration.py:40,130   (monkeypatch)
```

🔴 **NALAZ:** `ANTHROPIC_API_KEY` **NIJE u `backend/app/core/config.py`.** Taj modul
nabraja svaku env varijablu koju runtime proces koristi (DB, XMPP, JID-evi, JWT,
CORS) — i ključa među njima nema. Dakle: ključ postoji u `.env` i u razvojnom
okruženju, ali **nikad nije bio dio konfiguracijske površine FastAPI/SPADE procesa**.
Za Fazu 5 to znači jednu izmjenu u `config.py` bez obzira na providera.

**SDK je već ovisnost** — [`pyproject.toml`](backend/pyproject.toml): `"anthropic>=0.97.0"`.

**Wrapper već postoji i zreo je** — [`scripts/lib/api_client.py`](backend/scripts/lib/api_client.py):
retry s eksponencijalnim backoffom (`RateLimitError`, 5xx), eksplicitan
`max_retries=2` na SDK sloju, prompt caching (`cache_control: ephemeral`),
structured output kroz tool-use pattern, tipizirane iznimke
(`AnthropicAPIError`, `StructuredOutputError`), i konstante cijena za procjenu.

### B.2.2 Što bi OpenAI dodatno tražilo

| stavka | posljedica |
|---|---|
| **nova ovisnost** | `openai` u `pyproject.toml` + `uv.lock` — traži pitanje po CLAUDE.md („Što me pitati prije velikih promjena") |
| **novi ključ** | `OPENAI_API_KEY` — nabava, naplata, drugi račun |
| **nova env varijabla** | `.env`, `.env.example`, **i** `config.py`, **i** deployment (koji je javni URL za eval) |
| **novi wrapper** | `api_client.py` se ne može reciklirati — druge iznimke (`openai.RateLimitError` ≠ `anthropic.RateLimitError`), drugi oblik odgovora, drugi prompt-caching model |
| **novi način pada** | drugi rate-limit režim, drugi statusni kodovi, drugi retry-after; **drugi skup testova za mockanje** |
| **drugi primatelj osobnih podataka** | tekst suglasnosti iz B.1.3 mora imenovati OpenAI umjesto Anthropica — a to je **druga jurisdikcija i druga politika čuvanja** od one koju projekt već koristi za generiranje zadataka |
| **dvije vanjske usluge umjesto jedne** | rad bi morao opisati i obrazložiti obje |

### B.2.3 🔴 PREPORUKA: **Anthropic**, uz zapisano odstupanje od plana

Obrazloženje, po težini:

1. **Suglasnost.** Projekt već šalje podatke Anthropicu (generiranje zadataka, Faza 2),
   ali to su bili **sintetički** zadaci — nula studentskih podataka. Hint bi bio prvo
   slanje **studentskih** podataka. Ako se ide s varijantom A iz B.1.3, jedna usluga
   u tekstu je bitno lakše obraniti nego dvije. Ako se ide s varijantom B, ionako se
   ne šalje ništa studentsko — ali argument o jednom primatelju stoji.
2. **Nula novih ovisnosti** (CLAUDE.md pravilo) i **nula novog wrappera** — retry,
   caching i tool-use već su napisani, testirani i korišteni kroz cijelu Fazu 2.
3. **Jedan način pada.** Sustav koji ima jedan LLM-put ima jedan skup dijagnostika.
4. **Deployment.** Eval ide na javni URL bez nadzora; jedna tajna manje u okruženju
   je jedna manje koja može nedostajati u 3 ujutro.

**Model:** `claude-haiku-4-5` (200K kontekst, 1 $ / 5 $ po MTok). Hint je kratak,
latencijski osjetljiv zadatak — student čeka pred praznim panelom. Vidi §B.5.4 za
brojke i jedno **upozorenje o cachingu**.

**Odstupanje od plana se zapisuje**, ne prešućuje: plan §2.5 traži OpenAI/GPT-4o-mini.
U repou postoje dva traga te odluke, oba iz ranije faze:

- [`docs/faza-3-plan.md:240`](docs/faza-3-plan.md#L240) — *„HintAgent (6. agent) —
  `USE_LLM_HINTS` feature flag, GPT-4o-mini. Defer ako kasniš; rule-based `hints`
  tablica je fallback."*
- [`CLAUDE.md:17`](CLAUDE.md#L17) — *„LLM: Claude API (offline task gen), OpenAI
  GPT-4o-mini (opcionalno runtime hints)"*

Ako se preporuka prihvati, **oba** se mijenjaju u istom commitu s obrazloženjem, i
`CLAUDE.md` odjeljak „Agenti i njihove uloge" dobiva 6. agenta (workflow checklist).

---

## B.3 🔴 FALLBACK — tablica postoji, ali je PRAZNA

### B.3.1 Postoji li tablica? ✅ DA

[`models.py:349-368`](backend/app/db/models.py#L349-L368):

```python
# ============================================================
# HINTS
# ============================================================
class Hint(Base):
    __tablename__ = "hints"
    __table_args__ = (
        CheckConstraint("difficulty_min BETWEEN 1 AND 5", name="ck_hints_diffmin"),
        CheckConstraint("difficulty_max BETWEEN 1 AND 5", name="ck_hints_diffmax"),
        Index("idx_hints_error_concept", "error_type", "concept_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"))
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_min: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    difficulty_max: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="hr", server_default="hr")
```

Postoji od inicijalne migracije
([`ac6a5eeac6e5_initial_schema_16_tables.py:171-184`](backend/alembic/versions/ac6a5eeac6e5_initial_schema_16_tables.py#L171-L184)),
jedna je od 16 tablica koje `test_db_schema.py:23` provjerava. Indeks
`idx_hints_error_concept` na `(error_type, concept_id)` — dizajn je bio jasan:
**lookup po vrsti greške + konceptu**, s rasponom težine i jezikom.

### B.3.2 🔴 Koliko redaka? NULA

```
$ docker exec sql-tutor-pg-main psql -U tutor -d tutor_main -c "SELECT count(*) FROM hints;"
 hints_rows
------------
          0
(1 row)
```

```
$ grep -rn "Hint\b\|hints" backend/app/db/seed.py backend/app/db/seed_data.py
(nema pogodaka)
```

**Seed je ne dira. Nijedna skripta je ne puni. Nijedan kod je ne čita** — jedini
pogoci na `Hint` u `backend/` su definicija modela, migracija i popis tablica u testu.

### B.3.3 🔴 STANI-I-JAVI: fallback ne postoji

Plan tvrdi *„rule-based `hints` tablica je fallback"*. **Tvrdnja je danas neistinita
u praksi:** tablica je prazan omotač. HintAgent izgrađen na toj pretpostavci **pada
zajedno s LLM-om** — LLM timeout / nema ključa / rate limit → upit u `hints` vrati
nula redaka → nema što prikazati. Student vidi grešku umjesto pomoći, i to točno u
trenutku kad je zapeo.

Ovo je **preduvjet**, ne nice-to-have: bez fallbacka feature flag `USE_LLM_HINTS`
ima samo dva stanja (radi / ne postoji), a treba tri (LLM / rule-based / skriveno).

### B.3.4 Prijedlog minimalnog oblika

Tablica ne treba shemu mijenjati — `(error_type, concept_id NULL)` već dopušta
**dvorazinski lookup**:

```sql
-- 1. specifično: (error_type, concept_id) i difficulty u rasponu
-- 2. generičko:  (error_type, concept_id IS NULL)
-- 3. ako oba prazna → hint gumb je 'unavailable'
```

**Minimalni seed = 7 generičkih redaka**, po jedan za svaki `error_type` iz
taksonomije, `concept_id = NULL`, `language = 'hr'`, `difficulty_min=1`,
`difficulty_max=5`:

| `error_type` | smjer teksta (skica, ne finalni tekst) |
|---|---|
| `syntax_error` | upit je prazan ili neprepoznatljiv — provjeri je li editor prazan |
| `execution_error` | baza je odbila upit; poruka o grešci je u panelu ispod — počni od nje |
| `empty_result` | upit se izvršio, ali nije vratio nijedan redak — provjeri uvjete u `WHERE` |
| `wrong_columns` | vraćeni su drugi stupci od traženih — usporedi popis u `SELECT` s tekstom zadatka |
| `row_mismatch` | stupci su točni, ali skup redaka nije — provjeri filtriranje, spajanje i grupiranje |
| `timeout` | upit je predugo trajao — provjeri ima li nenamjeran križni spoj |
| `unsupported_eval` | ovaj tip zadatka sustav još ne ocjenjuje automatski |

**Zašto 7, a ne 210 (7 × 30 koncepata):** generički sloj je **garancija da fallback
uvijek nešto vrati**. Specifični `(error_type, concept_id)` redci dodaju se poslije,
za koncepte koji se u evalu pokažu kao usko grlo — i to je prirodan posao za
istu offline generacijsku infrastrukturu iz Faze 2 (`AnthropicClient` +
`generate_structured_output` protiv `Hint` sheme), s ljudskom provjerom, kao što je
rađeno za zadatke.

**Kritični detalj:** i generički i specifični tekst **ne smiju sadržavati rješenje**
— isti invarijant koji već vrijedi za `attempts.detail`
([models.py:190-192](backend/app/db/models.py#L190-L192): *„NIKAD ne smije sadržavati
`expected_query` ni sadržaj očekivanih redaka"*). Za seedani tekst to je lako
osigurati; za LLM-generirani specifični tekst treba **validator prije unosa**, ne
povjerenje.

---

## B.4 ŠTO SE MIJENJA U ZAMRZNUTOM BACKENDU

### B.4.1 `hint_requested` — kako postaje `True`

Danas je hardkodiran ([`persistence.py:78`](backend/agents/persistence.py#L78)):

```python
        row = Attempt(
            user_id=user_id,
            task_id=task_id,
            submitted_query=submitted_query,
            ...
            attempt_number=attempt_number,
            xp_awarded=0,
            hint_requested=False,          # ← :78
        )
```

🔴 **Ključni nalaz o vremenskom redoslijedu:** student traži hint **PRIJE** predaje.
U trenutku zahtjeva za hintom **attempt red još ne postoji** — `persist_attempt` se
zove tek iz EvaluatorAgenta, nakon `POST /attempt`. Zato **hint ruta ne može
UPDATE-ati `attempts.hint_requested`** — nema što ažurirati.

**Jedini zdrav put:** zastavica putuje s predajom.

1. **`AttemptRequest` dobiva polje** ([`schemas.py:21-24`](backend/app/api/schemas.py#L21-L24)):

   ```python
   class AttemptRequest(BaseModel):
       task_id: int
       submitted_query: str
       hint_requested: bool = False        # ← novo, default False (unatrag kompatibilno)
   ```

   Default `False` znači da **stari klijent i dalje radi** — bitno, jer `schema.d.ts`
   se regenerira, a stari build ne šalje polje.

2. **`persist_attempt` dobiva parametar**, `hint_requested=False` postaje
   `hint_requested=hint_requested`. Potpis se mijenja s defaultom, pa postojeći
   pozivi u testovima (`test_persistence.py:133,238`) i dalje prolaze.

3. **Lanac nosi zastavicu:** `post_attempt` → `submit-attempt` payload →
   `EvaluateState` → `evaluate-query` payload → EvaluatorAgent → `persist_attempt`.
   Danas payload nosi `{user_id, task_id, submitted_query}`
   ([coordinator.py:267-271](backend/agents/coordinator.py#L267-L271)); dodaje se
   četvrto polje. **To je izmjena u FIPA payloadu** → po CLAUDE.md traži pitanje
   prije izvedbe.

4. **Frontend drži stanje:** „je li za ovaj zadatak zatražen hint otkad je zadnji
   put predano". Reset na `retrySameTask` i na promjenu `task.id` (postojeći `key`
   reset u [TaskPage.tsx:112](frontend/src/pages/TaskPage.tsx#L112) već radi po tasku).

**Alternativa koja je odbačena:** zaseban `hint_log` red umjesto zastavice na
attemptu. Odbijena jer bi značila **novu tablicu = migracija = izmjena sheme**, a
kolona koja točno to znači već postoji od Faze 1 i već se izvozi u eval podatke
([`export_eval_data.py:87`](backend/scripts/export_eval_data.py#L87)). Za rad je
korisna upravo veza *hint ↔ ishod tog pokušaja*, koju zastavica na attemptu daje
izravno.

### B.4.2 Nova ruta ili proširenje postojeće? → **NOVA**

Postojeće rute su neupotrebljive: `/attempt` je scored predaja, `/run` je čisti
sandbox exec, `/next-task` je preporuka. Hint je zaseban čin s vlastitim ugovorom.

**Presedan koji ruta slijedi:** `GET /next-task` —
*„izravan recommend-next kroz bridge (bez FSM-a)"*
([routes.py:227-228](backend/app/api/routes.py#L227-L228)). Isti oblik, s POST-om
jer nosi tijelo.

**Prijedlog ugovora:**

```python
class HintRequest(BaseModel):
    task_id: int
    #: Opcionalno — šalje se SAMO ako odluka iz §B.1 padne na varijantu A.
    #: Pod varijantom B polje ne postoji u ugovoru (ne „postoji i ignorira se").
    submitted_query: str | None = None


class HintResponse(BaseModel):
    hint_text: str
    #: "llm" | "rule" — UI ga ne prikazuje, ali eval izvoz treba razlučiti izvore
    source: str
    #: Koncept na koji je hint vezan (None ako je generički fallback)
    concept: str | None = None
    #: Preostalo hintova u prozoru; None = limit se ne primjenjuje
    remaining: int | None = None
```

Ruta: `POST /hint`, `user: User = Depends(get_current_user)` — `user_id` iz tokena,
klijent ga ne bira (isti obrazac kao `AttemptRequest`, Faza 4.0b.2).

**Kodovi odgovora:**

| stanje | HTTP | tijelo |
|---|---|---|
| LLM uspio | 200 | `source="llm"` |
| LLM pao, fallback našao redak | 200 | `source="rule"` |
| LLM pao, fallback prazan | **503** | `detail="hint_unavailable"` |
| iskorišten limit | **429** | `detail="hint_rate_limited"` |
| flag isključen | **503** | `detail="hints_disabled"` |
| HintAgent ne odgovara | **504** | `detail="hint_timeout"` |

### B.4.3 🔴 `schema.d.ts` — TOČNO koja polja se dodaju

`schema.d.ts` se generira iz živog `/openapi.json` (`npm run gen:api`), pa je popis
mehanička posljedica gornjeg ugovora. **Frontend zna konzumirati samo ono što je u
ugovoru** — zato je popis iscrpan:

**Izmijenjene sheme:**

| shema | izmjena |
|---|---|
| `components["schemas"]["AttemptRequest"]` | **+ `hint_requested?: boolean`** (default `false`, dakle opcionalno u TS-u) |
| `components["schemas"]["MeResponse"]` | **+ `hints_enabled: boolean`** — vidi obrazloženje ispod |

**Nove sheme:**

| shema | polja |
|---|---|
| `components["schemas"]["HintRequest"]` | `task_id: number` · `submitted_query?: string \| null` *(samo varijanta A)* |
| `components["schemas"]["HintResponse"]` | `hint_text: string` · `source: string` · `concept?: string \| null` · `remaining?: number \| null` |

**Novi path:** `paths["/hint"]["post"]`.

**Nepromijenjeno:** `AttemptResponse`, `FeedbackModel`, `TaskDetailResponse`,
`AttemptItem` (već ima `hint_requested: boolean`, `schema.d.ts:293-294` — polje je
u ugovoru od Faze 1, samo je uvijek bilo `false`).

🔴 **Zašto `hints_enabled` ide na `MeResponse`, a ne na 404/503 s rute.** Stanje
`unavailable` iz `faza-4.7-korak-0.md` §D.4 traži da se gumb **tiho sakrije**. Ako
se stanje otkriva tek klikom, student vidi gumb → klikne → dobije grešku. To je
suprotno od „tiho sakrij". `/me` se dohvaća jednom pri prijavi i već je u auth
kontekstu, pa je zastavica dostupna prije prvog rendera Task ekrana.

### B.4.4 🔴 FIPA lanac — blokira li HintAgent postojeći put?

**Postojeći put** ([coordinator.py:7-8](backend/agents/coordinator.py#L7-L8)):

```
RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND → (natrag na RECEIVE)
```

**Kritična činjenica o konkurenciji** ([coordinator.py:20-25](backend/agents/coordinator.py#L20-L25)):

```
KONKURENCIJA (svjesna MVP odluka — GATE 2):
  Sekvencijalna orkestracija, jedan tutoring-ciklus po instanci. SPADE FSMBehaviour
  ima jedan mailbox queue i izvodi stanja strogo redom, pa se SVI studentski flowovi
  globalno serijaliziraju kroz jednu instancu.
```

🔴 **Zato: ako hint prođe kroz Coordinatorov FSM, blokira SVE studente.**
LLM poziv traje sekunde (§B.5.1). Kroz FSM to znači da svaki `POST /attempt` bilo
kojeg drugog studenta čeka taj poziv. Uz `DEFAULT_UPDATE_TIMEOUT = 5.0` i
`GATEWAY_TIMEOUT = 15`, jedan spor hint može gurnuti tuđu predaju u 504. **To bi bila
regresija na eval-verificiranom putu** — i to najgore vrste, jer se pokazuje samo
pod konkurencijom, dakle upravo u evalu, a ne u ručnom testiranju.

✅ **Rješenje koje regresiju izbjegava: hint NE ulazi u Coordinatorov FSM.**
Ide izravno gateway → HintAgent, po presedanu `/next-task`.

**Predloženi lanac:**

```
POST /hint
  → bridge.register()                       → (cid, future)
  → gateway.send_fipa(to=AGENT_HINT_JID,
                      ontology="request-hint",
                      performative=REQUEST,
                      payload={user_id, task_id, ...},
                      cid=cid)
  → HintAgent (CyclicBehaviour): DB read → LLM → fallback → build hint
  → INFORM natrag na gateway JID, isti cid, ontology="request-hint"
  → GatewayAgent._Resolve → bridge.resolve(cid, payload)
  → bridge.wait(cid, timeout=HINT_TIMEOUT)  → HTTP 200
```

**Performativi:**

| smjer | performativ | ontologija | kada |
|---|---|---|---|
| gateway → Hint | `request` | `request-hint` | uvijek |
| Hint → gateway | `inform` | `request-hint` | hint sastavljen (LLM ili rule) |
| Hint → gateway | `failure` | `request-hint` | LLM pao **i** fallback prazan → 503 |
| Hint → gateway | `refuse` | `request-hint` | limit iskorišten → 429 |

`refuse` i `failure` već postoje u `Performative`
([messages.py:14-19](backend/agents/messages.py#L14-L19)) i **dosad nemaju nijednog
potrošača** — hint bi bio prvi. To je uredno: skup je definiran kao FIPA-ACL
podskup, ne kao popis onoga što se koristi.

`Ontology` dobiva `REQUEST_HINT = "request-hint"`
([messages.py:25-31](backend/agents/messages.py#L25-L31)).

**`correlation_id`:** novi `uuid4` iz `bridge.register()` po zahtjevu. **Nije** vezan
uz `attempt_id` — attempt u tom trenutku ne postoji (§B.4.1). Trag u
`agent_messages_log` bit će zaseban razgovor s vlastitim cid-om.

**Izmjene koje ovaj put traži:**

| datoteka | izmjena |
|---|---|
| `agents/jids.py` | `"hint": (config.AGENT_HINT_JID, config.AGENT_HINT_PASSWORD)` |
| `app/core/config.py` | `AGENT_HINT_JID`, `AGENT_HINT_PASSWORD`, `ANTHROPIC_API_KEY`, `USE_LLM_HINTS`, `HINT_TIMEOUT`, limit konstante |
| `app/bridge/gateway_agent.py` | `setup()`: template `t_hint` dodan u `t_attempt \| t_recommend` ([gateway_agent.py:69-76](backend/app/bridge/gateway_agent.py#L69-L76)) |
| `agents/messages.py` | `Ontology.REQUEST_HINT` |
| `agents/hint_agent.py` | **nov** |
| `docker/prosody/` | registracija `hint@localhost` |
| `.env` / `.env.example` | `AGENT_HINT_PASSWORD`, `USE_LLM_HINTS` |
| `app/main.py` (lifespan) | start HintAgenta unutar uvicornovog loopa (invarijant iz [agent_bridge.py:29-31](backend/app/bridge/agent_bridge.py#L29-L31)) |

🔴 **`coordinator.py` se NE DIRA.** `_coordinator_template()` propušta samo tri
ontologije ([coordinator.py:410-418](backend/app/bridge/../../backend/agents/coordinator.py#L410-L418)),
i `request-hint` nije među njima — poruka mu ni ne može doći u queue. `RECEIVE →
EVALUATE → UPDATE → RECOMMEND → RESPOND` ostaje **byte-identičan**.

**Preostali dodir eval-verificiranog puta:** samo `persistence.py` (parametar) i
`evaluate-query` payload (četvrto polje) iz §B.4.1. Oba se moraju re-verificirati na
živom lancu, kao što je rađeno za panel s ocjenom u 4.7.

---

## B.5 OTPORNOST

### B.5.1 Timeout prema LLM-u

**Postojeći proračun timeouta u sustavu:**

```
GATEWAY_TIMEOUT        = 15.0 s   (config.py:63 — MORA biti > Coordinator timeouta)
DEFAULT_UPDATE_TIMEOUT =  5.0 s
DEFAULT_RECOMMEND_TIMEOUT = 5.0 s
DEFAULT_RECEIVE_TIMEOUT = 30.0 s
statement_timeout (sandbox) = 5 s
```

**Prijedlog:** `HINT_LLM_TIMEOUT = 8.0` (SDK-ov `timeout=` na klijentu),
`HINT_TIMEOUT = 12.0` (bridge `wait`). Oba **ispod** `GATEWAY_TIMEOUT = 15`, po
istom obrascu koji komentar u `config.py:61-62` propisuje za Coordinator.

**Što se događa nakon:**

```
LLM > 8 s   → SDK APITimeoutError → HintAgent hvata → fallback lookup u `hints`
              → INFORM sa source="rule"                            → 200
fallback prazan → FAILURE                                          → 503
HintAgent uopće ne odgovori > 12 s → bridge.wait TimeoutError      → 504
```

🔴 **HintAgent ne smije retry-ati unutar zahtjeva.** `AnthropicClient` ima
`DEFAULT_MAX_RETRIES = 3` s backoffom 1/2/4 s **plus** SDK `max_retries=2`
([api_client.py:45-49](backend/scripts/lib/api_client.py#L45-L49)) — worst case
9 poziva. Za offline generaciju je to ispravno; za hint bi značilo da student čeka
desetke sekundi. Hint mora koristiti **`max_retries=0` na SDK klijentu i nula
CLI-retryja** — jedan pokušaj, pa fallback. To je izmjena u konfiguraciji klijenta,
ne u wrapperu (wrapper prima `api_key` i `model`; treba mu i `max_retries`).

### B.5.2 Rate limit

🔴 **U projektu NE POSTOJI nijedan uzorak rate-limitiranja.**

```
$ grep -rniE "rate.?limit|slowapi|limiter|@cache|lru_cache|functools.cache" backend/ --include=*.py
backend/tests/test_api_client.py:41,42   ← anthropic RateLimitError (dolazni, ne odlazni)
backend/scripts/lib/api_client.py:8,47,92 ← isto
```

Sve tri pogotka su o **hvatanju** Anthropicovog rate-limita, ne o **nametanju**
vlastitog. Nema `slowapi`, nema middlewarea, nema brojača.

**Prijedlog — bez nove ovisnosti i bez nove tablice:**

Broji se **u bazi, iz podataka koji već postoje**. Kad je `hint_requested` na
attemptu (§B.4.1), broj hintova po korisniku po prozoru je:

```sql
SELECT count(*) FROM attempts
WHERE user_id = :uid AND hint_requested = true
  AND created_at > now() - interval '1 hour';
```

🔴 **Ali to podbroji** — hint zatražen a zadatak nikad predan ne ostavlja trag.
Za pošten limit treba brojati **zahtjeve**, ne predaje.

**Dva izvedena prijedloga, po cijeni:**

| pristup | trošak | preživljava restart? |
|---|---|---|
| **(a) in-memory brojač** `dict[user_id, list[timestamp]]` u HintAgentu, prozor 1 h | nula izmjena sheme, ~20 linija | ❌ **ne** — restart resetira limit |
| **(b) brojanje iz `agent_messages_log`** — `sender = gateway`, `receiver = hint JID`, `created_at > now() - 1h`, `content->>'user_id' = :uid` | nula izmjena sheme, jedan SQL | ✅ **da** |

**Preporuka: (b).** Log već upisuje svaki `request-hint` s `user_id` u `content`
JSONB ([base.py:64-89](backend/agents/base.py#L64-L89) + `send_fipa`
[gateway_agent.py:104-110](backend/app/bridge/gateway_agent.py#L104-L110)), indeks
`idx_agent_messages_created` postoji, i vrijednost preživljava restart kontejnera.

🔴 **Ali nosi posljedicu za #46:** taj JSONB tada nosi još jedan zapis po korisniku
koji se **ne može obrisati po osobi** (`agent_messages_log` nema `user_id` kolonu).
Errata #46 procjenjuje ~7 400 zapisa za eval volumen; hint bi dodao red veličine
+600 (jedan `request` + jedan `inform` po hintu). To **ne mijenja narav** #46 (već je
blokator), ali ga treba spomenuti u #59.

**Predložena vrijednost limita:** **10 hintova po korisniku po satu.** Obrazloženje:
eval sesija je ~30 pokušaja; 10/h je dovoljno da hint bude stvarna pomoć, a dovoljno
malo da spriječi i slučajnu petlju u frontendu i namjerno crpljenje ključa.

### B.5.3 Cache po `(error_signature, skill_level)`

Plan traži cache po tom ključu. Realizacija u ovom sustavu:

**Ključ.** `error_signature` iz plana najbliže odgovara postojećem
misconception kodu `"{primary_concept}__{error_type}"`
([misconception_logic.py:3-5](backend/agents/misconception_logic.py#L3-L5)).
S `skill_level` u 3 razreda ključ postaje:

```
(primary_concept, error_type, p_L_bucket, task_id)
```

`task_id` je nužan **ako opis zadatka ulazi u prompt** — inače bi dva različita
zadatka istog koncepta dijelila isti hint. Bez `task_id`: 30 × 7 × 3 = **630**
ključeva. S `task_id`: gornja granica 80 × 7 × 3 = **1 680**.

**Gdje bi živio:**

| opcija | preživljava restart? | ocjena |
|---|---|---|
| in-memory `dict` u HintAgentu | ❌ | najjeftinije; 1 680 kratkih stringova ≈ desetak kB |
| tablica `hints` s `concept_id` + `error_type` | ✅ | **već postoji shema za to** |

🔴 **Preporuka: cache = upis u `hints`, ne zaseban sloj.** Tablica iz §B.3 ima
točno `(error_type, concept_id, hint_text, difficulty_min/max, language)`. LLM-generiran
hint koji prođe validator (bez rješenja) upisuje se kao redak; sljedeći student s
istim `(error_type, concept)` dobiva ga **iz baze, bez LLM poziva**. Time se fallback
i cache **spajaju u jedan mehanizam** koji sam sebe puni.

**Cijena te odluke, poštena:** hint prestaje biti personaliziran po `p_L` (shema nema
kolonu za razinu — `difficulty_min/max` se odnosi na **težinu zadatka**, ne na znanje
studenta). Ako je personalizacija po BKT-u dio doprinosa rada, treba ili
in-memory cache uz živi LLM poziv, ili novu kolonu (= migracija = pitanje korisniku).
**Odluka za stage 5.1.**

**Preživljava li restart kontejnera:** DB da, in-memory ne. Za eval bez nadzora
(kontejner se može restartati) DB varijanta je jedina koja ne gubi ni cache ni brojač.

### B.5.4 Trošak

**Procjena veličine jednog poziva** (varijanta B iz §B.1, dakle bez `submitted_query`):

| dio | ulaz (tok) |
|---|---|
| sustavski prompt (pedagoška uputa + shema `ecommerce_v1` + zabrana rješenja) | ~1 500 |
| korisnička poruka (opis zadatka, koncept, `error_type`, `p_L`, `attempt_number`) | ~300 |
| **ukupno ulaz** | **~1 800** |
| izlaz (2–3 rečenice na hrvatskom) | **~120** |

**Po hintu, `claude-haiku-4-5` (1 $ / 5 $ po MTok), bez cachinga:**

```
ulaz:  1 800 × 1 $/1M  = 0,0018 $
izlaz:   120 × 5 $/1M  = 0,0006 $
                       = 0,0024 $ / hint
```

**Po hintu, `claude-sonnet-5` (3 $ / 15 $ po MTok, standardno):**

```
ulaz:  1 800 × 3 $/1M  = 0,0054 $
izlaz:   120 × 15 $/1M = 0,0018 $
                       = 0,0072 $ / hint
```

**Za eval volumen (20 sudionika × 30 pokušaja = 600 pokušaja):**

| scenarij | Haiku 4.5 | Sonnet 5 |
|---|---|---|
| hint na **svakom** pokušaju (600) | **1,44 $** | **4,32 $** |
| hint na ~30 % pokušaja (180) | **0,43 $** | **1,30 $** |
| uz cache/`hints` popunjenost 50 % | **0,22–0,72 $** | **0,65–2,16 $** |

**Zaključak: trošak nije faktor u odluci.** I najskuplji scenarij je ispod 5 $, dakle
unutar reda veličine starter kredita koji je Faza 2A već koristila
([`faza-2a-plan.md:900`](docs/faza-2a-plan.md#L900)).

🔴 **Upozorenje o prompt cachingu — Haiku ne može cache-irati ovaj prompt.**
Minimalni cache-abilan prefiks ovisi o modelu: **Haiku 4.5 traži 4 096 tokena**,
dok Sonnet 5 traži 1 024. Sustavski prompt od ~1 500 tokena je **ispod Haikuova praga**
— `cache_control` se tiho ne primjenjuje (`cache_creation_input_tokens: 0`, bez greške).
`AnthropicClient.generate` **bezuvjetno postavlja** `cache_control: ephemeral` na
sustavski blok ([api_client.py:66-73](backend/scripts/lib/api_client.py#L66-L73)) —
na Haikuu bi to bio mrtav kod, ne kvar. Praktična posljedica: **caching ne ulazi u
odluku Haiku↔Sonnet** jer je ušteda ionako ispod 5 $ ukupno. Ako se sustavski prompt
ikad naraste preko 4 096 tokena, caching se na Haikuu „uključi sam" — što treba
**izmjeriti** (`usage.cache_read_input_tokens`), ne pretpostaviti (poučak N-18/#55).

**Preporuka modela: `claude-haiku-4-5`.** Latencija je ovdje jedini stvarni kriterij
— student čeka pred praznim panelom, a razlika u kvaliteti za 2–3 rečenice hinta na
hrvatskom je marginalna spram razlike u odzivu. Ako se u stage 5.1 pokaže da hintovi
nisu dovoljno pedagoški precizni, prelazak na `claude-sonnet-5` je promjena jednog
stringa i +3 $ na cijeli eval.

### B.5.5 🔴 `USE_LLM_HINTS = false` → gumb se TIHO SKRIVA

**Potvrđeno izvedivo bez izmjene layouta — IZMJERENO.** Vidi §B.6: kartica ima
**identičnu visinu** s gumbom i bez njega, na svakoj testiranoj širini. Skrivanje
gumba ne pomiče editor ni panel s ocjenom.

**Mehanizam:** `hints_enabled` iz `/me` (§B.4.3) → uvjetni render prvog djeteta
akcijskog reda. `justify-end` na vanjskom flexu znači da Run/Submit grupa ostaje
**prislonjena desno** bez obzira postoji li lijevi element — nema „rupe" gdje je gumb
bio.

```tsx
{hintsEnabled && <Button variant="outline" …>Zatraži hint</Button>}
<div className="flex items-center gap-2">{/* Run + Submit — nepromijenjeno */}</div>
```

---

## B.6 ŠTO JE VEĆ RIJEŠENO — potvrda nakon redizajna

`faza-4.7-korak-0.md` §D je zaključio: gumb ide kao **prvi child vanjskog flexa**
u akcijskom redu, varijanta `ghost`/`outline` (nikad `default`), neutralna boja
(`border-border` + `bg-muted`), sadržaj u **zasebnom slotu** iznad `FeedbackPanel`a
(ne grana `submitSlot` enuma), i tablica stanja idle/loading/success/error/
unavailable/rate-limited.

### B.6.1 Struktura je PREŽIVJELA redizajn ✅

Akcijski red se pomaknuo `:337` → **`:417`**, ali je **strukturno nepromijenjen**
([TaskPage.tsx:417-439](frontend/src/pages/TaskPage.tsx#L417-L439)):

```tsx
<div className="flex flex-wrap items-center justify-end gap-3">   // ← :417 (bilo :337)
  <div className="flex items-center gap-2">                        // ← :418 Run+Submit
```

Vanjski `justify-end` s `gap-3`, Run/Submit grupa i dalje u vlastitom `div`u.
**Pretpostavka §D.3 stoji.** Editor je i dalje `h-[420px] … xl:h-[520px]`
([TaskPage.tsx:408](frontend/src/pages/TaskPage.tsx#L408)), `submitSlot` je i dalje
ekskluzivan enum ([TaskPage.tsx:441-471](frontend/src/pages/TaskPage.tsx#L441-L471)),
`Button` varijante `outline`/`ghost` postoje
([button.tsx:25-30](frontend/src/components/ui/button.tsx#L25-L30)).

### B.6.2 🔴 IZMJERENO — diše li red s trećim elementom?

**Metoda.** Harness s **pravim buildanim CSS-om** (`vite build` → `dist/assets/
index-8xMgi9Nk.css`, lokalni `@fontsource` fontovi), replika DOM podstabla
AppShell → `main` → TaskPage grid → desni Card → akcijski red, s klasama kopiranim
doslovno iz `AppShell.tsx` / `TaskPage.tsx` / `card.tsx` / `button.tsx` / `kbd.tsx`.
Mjereno Playwrightom (`getBoundingClientRect`) nakon `document.fonts.ready`.

**Kontrola ispravnosti harnessa:** izmjerena širina kartice na 1280 px je
**555,34 px**; aritmetika iz grida (`1280 − 240 sidebar − 64 padding − 24 gap` →
7/12) daje **555,33 px**. Poklapanje potvrđuje da harness reproducira pravi layout,
a ne aproksimaciju.

**Rezultat — gumb „Zatraži hint" (`outline`, `Lightbulb` + tekst):**

| viewport | širina kartice | visina kartice BEZ → S hintom | visina reda | slack u redu |
|---|---|---|---|---|
| 1920 | 928,67 | 640 → **640** ✅ | 44 px ✅ | **467,14 px** |
| 1536 | 704,66 | 640 → **640** ✅ | 44 px ✅ | **243,13 px** |
| 1440 | 648,66 | 640 → **640** ✅ | 44 px ✅ | **187,13 px** |
| 1360 | 602,00 | 640 → **640** ✅ | 44 px ✅ | **140,47 px** |
| **1280** (xl, najuži zbog 7/12 grida) | 555,34 | 640 → **640** ✅ | 44 px ✅ | **93,81 px** |
| 1279 (jednostupčano) | 975,00 | 540 → **540** ✅ | 44 px ✅ | **513,47 px** |
| 1024 | 720,00 | 540 → **540** ✅ | 44 px ✅ | **258,47 px** |
| **768** (md, editor se tek pojavljuje) | 464,00 | 540 → **540** ✅ | 44 px ✅ | 🟡 **2,47 px** |

**Sastavnice na 1280 px:** red 523,34 px · hint gumb 119 px · `gap-3` = 12 px ·
Run+Submit grupa 298,53 px.

**Presuda:**

✅ **Red diše s trećim elementom. Visina kartice se NE mijenja ni na jednoj testiranoj
širini. Nema wrapa.** Isto vrijedi u oba smjera — skrivanje gumba (stanje
`unavailable`, §B.5.5) također ne mijenja visinu.

🟡 **ALI: na 768 px slack je 2,47 px.** To je granica, ne rezerva.

### B.6.3 🔴 NALAZ N-20 — natpis hint gumba ima proračun od 2,47 px

Drugi krug mjerenja, na 768 px (najuža širina na kojoj editor uopće postoji,
`hidden md:block`):

| natpis | širina gumba | slack | visina reda | visina kartice | |
|---|---|---|---|---|---|
| „Hint" | 77 px | +44,47 px | 44 px | 540 px | ✅ |
| **„Zatraži hint"** (preporuka §D.3) | **119 px** | **+2,47 px** | 44 px | 540 px | ✅ |
| „Zatraži savjet" | 132 px | −10,53 px | **100 px** | **596 px** | 🔴 WRAP |
| „Zatraži pomoć" | 137 px | −15,53 px | **100 px** | **596 px** | 🔴 WRAP |
| „Trebam pomoć" | 140 px | −18,53 px | **100 px** | **596 px** | 🔴 WRAP |
| „Zatraži hint (1/3)" | 148 px | −26,53 px | **100 px** | **596 px** | 🔴 WRAP |

Na 800 px viewporta **svi** natpisi stanu (slack 5,47–76,47 px). Problem postoji
**isključivo u pojasu 768–~790 px.**

**Posljedica wrapa je mjerljiva:** akcijski red 44 → **100 px**, kartica 540 →
**596 px** (+56 px). Editor se ne pomiče (iznad je), ali se cijeli desni panel
produži i `FeedbackPanel` padne niže — točno ono što §D.3 zabranjuje.

**Tri razrješenja (odluka za stage 5.2, ne za ovaj korak):**

1. **Zaključati natpis na „Zatraži hint"** i to zapisati kao invarijantu s mjerenjem.
   Najjeftinije, ali krhko — sljedeći tko „poboljša" copy sruši layout, a ništa ga
   ne zaustavlja.
2. **Responzivan natpis:** `<span className="hidden lg:inline">Zatraži&nbsp;</span>hint`.
   Ispod `lg` gumb je „hint" (77 px, slack 44 px), iznad pun natpis. Rješava pojas
   trajno, cijena je jedan uvjetni raspon.
3. **Ikona-only ispod `lg`** (`size="icon"`, 44 px, WCAG 2.5.5 zadovoljen), s
   `aria-label="Zatraži hint"`. Najviše slacka, ali gubi tekstualnu naznaku — a
   `faza-4.7-korak-0.md` §D.3 izričito traži tekstualni natpis.

🟡 **Preporuka: (2).** Zadržava tekst gdje ima mjesta, a mjerenje pokazuje da ispod
`lg` mjesta nema pouzdano. Broj 2,47 px nije rezerva — to je zaokruživanje.

**Ostatak §D stoji nepromijenjeno:** varijanta (`outline`), boja (`border-border` +
`bg-muted`), zaseban slot iznad `FeedbackPanel`a, tablica stanja. Stanje
`unavailable` sada ima obrazac (§B.5.5), stanje `rate-limited` ima ugovor
(429 + `remaining` u `HintResponse`, §B.4.2).

---

# G — GATE: četiri neodgovorene točke + jedna kontradikcija

> Dopuna od 2026-08-11, isti korak, ista grana. **§C je revidiran prema G1/G5/G6** —
> stara verzija stagea više ne vrijedi tamo gdje se razlikuje.

---

## G1 🔴 KONTRADIKCIJA: `error_type` u trenutku traženja hinta

Kontradikcija je stvarna i moja: §B.4.1 tvrdi da attempt red ne postoji kad se hint
traži, a §B.1.4 računa 1 260 situacija oslanjajući se na `error_type`. Razrješenje:
**oba su točna, ali za različite zadatke.** `error_type` ne dolazi iz *tekućeg*
pokušaja (koji još ne postoji) nego iz **prethodnog** pokušaja na **istom** zadatku.
Zadatak koji student nikad nije predao nema nijedan — i to je treći slučaj koji §B
nije razdvojio.

### G1.1 Postoji li put do `error_type` prethodnog attempta? ✅ DA — i presedan je već u kodu

`Attempt` nosi sve što treba: `user_id`, `task_id`, `error_type`, `attempt_number`,
`created_at` ([models.py:184-199](backend/app/db/models.py#L184-L199)), a
`Index("idx_attempts_user_task", "user_id", "task_id")`
([models.py:177](backend/app/db/models.py#L177)) je točno indeks za taj upit.

**Presedan istog oblika već postoji** — `solved` provjera u `_read_task_detail`
([routes.py:350-360](backend/app/api/routes.py#L350-L360)):

```python
        solved = (
            session.scalar(
                select(Attempt.id)
                .where(
                    Attempt.user_id == user_id,
                    Attempt.task_id == task_id,
                    Attempt.is_correct.is_(True),
                )
                .limit(1)
            )
            is not None
        )
```

Upit koji HintAgent treba razlikuje se u dvije riječi — `Attempt.error_type` umjesto
`Attempt.id`, i `order_by(Attempt.attempt_number.desc())` umjesto `is_correct` filtra:

```python
last = session.execute(
    select(Attempt.error_type, Attempt.detail, Attempt.attempt_number)
    .where(Attempt.user_id == user_id, Attempt.task_id == task_id)
    .order_by(Attempt.attempt_number.desc())
    .limit(1)
).first()          # None ⟺ netaknut zadatak
```

**Dokaz da put nije samo teorijski:** `prior_correct_solve_exists` u
`gamification_persistence.py` (pozvan iz `coordinator.py:147`) već radi upravo takav
pogled unatrag po `(user_id, task_id, attempt_number)`.

**Nula izmjena sheme, nula migracije, nula novog indeksa.**

### G1.2 Što payload sadrži na NETAKNUTOM zadatku — polje po polje

| polje | vrijednost | izvor |
|---|---|---|
| `task_id` | ✅ ima | tijelo zahtjeva |
| `task.description` | ✅ ima | `tasks.description` |
| `task.difficulty` | ✅ ima (1–5) | `tasks.difficulty` |
| `primary_concept.code` | ✅ ima | `task_concepts` + `concepts` |
| `p_L` primarnog koncepta | 🟡 **ima samo ako je student već radio TAJ koncept** na drugom zadatku; inače nema `skill_mastery` reda → tier default | `skill_mastery.p_l` |
| `attempt_number` | ❌ **nema** (0) | — |
| `error_type` | ❌ **NEMA — `None`** | — |
| `detail` | ❌ **nema** | — |

Dakle na netaknutom zadatku hint raspolaže **isključivo statičkim podacima o zadatku
+ (možda) procjenom znanja koncepta**. Ništa o tome što je student napravio, jer
nije napravio ništa.

### G1.3 🔴 Kardinalnost, zasebno po slučaju

Prvo korekcija ulaza u račun iz §B.1.4 — **`unsupported_eval` je nedostižan na
aktivnim zadacima.** `UNSUPPORTED_CONCEPTS = {explain_plan, index_usage}`
([evaluation.py:38](backend/agents/evaluation.py#L38)), a izmjereno:

```sql
SELECT c.code FROM concepts c WHERE c.id NOT IN (
  SELECT tc.concept_id FROM task_concepts tc
  JOIN tasks t ON t.id=tc.task_id AND t.is_active WHERE tc.is_primary);
--  column_alias · explain_plan · index_usage · join_condition
```

`explain_plan` i `index_usage` **nemaju nijedan aktivan primarni zadatak** (a od 4.4-0f
neaktivan task je 404, [routes.py:326](backend/app/api/routes.py#L326)). Dosežnih
`error_type` vrijednosti je dakle **6**, ne 7. Uz to: **26 od 30 koncepata** nosi
aktivne primarne zadatke, **80** zadataka ukupno.

**Slučaj A — zadatak s ≥1 prethodnim pokušajem:**

| ključ | kardinalnost |
|---|---|
| po **konceptu**: 26 × 6 × 3 (`p_L` razred) | **468** |
| po **zadatku** (ako opis zadatka ulazi u prompt): 80 × 6 × 3 | **1 440** |

**Slučaj B — netaknut zadatak (nula attempta):**

| ključ | kardinalnost |
|---|---|
| po **konceptu**: 26 × 3 | **78** |
| po **zadatku**: 80 × 3 | **240** |

> ## ⟳ 🔴 §G1.3 i §G1.4 — **POVUČENI 2026-08-11**
>
> Odlukom korisnika hint je dostupan tek nakon barem jednog netočnog pokušaja na tom
> zadatku, pa **slučaj B (netaknut zadatak) više ne postoji** — a s njim ni 240
> predgeneriranih tekstova ni grananje po `error_type IS NULL`. Prijedlog ispod ostaje
> zapisan jer je iz njega izvedena kardinalnost slučaja A (§H2.3, §G4.3) i jer je
> mjerenje `unsupported_eval`/26-koncepata i dalje na snazi. **Mehanika otključavanja
> je sada §H3.**

🔴 ~~**STANI-I-JAVI (G1.3): slučaj „prvi pokušaj" je ISPOD praga informativnosti.**~~ *(povučeno)*

**240 kombinacija po zadatku, 78 po konceptu — oboje ispod ~300.** Izričito:

> **Hint za prvi pokušaj na zadatku je predgenerabilan offline. Runtime LLM poziv za
> njega ne nosi informaciju** — ulaz je u cijelosti statički (`description`,
> `difficulty`, `concept`) plus jedan od tri razreda `p_L`, i ne sadrži nijedan
> podatak o tome što je taj student napravio. Dva različita studenta na istom zadatku
> u istom `p_L` razredu dobili bi **isti** hint, samo bi ga svaki platio zasebnim
> pozivom i zasebnom sekundom čekanja.

Isti račun kaže i **kolika je gornja granica cijele generacije**: 240 hintova × cijena
iz §B.5.4 = **0,58 $ (Haiku)** ili **1,73 $ (Sonnet 5)** za predgeneriranje *svakog
mogućeg* hinta prvog pokušaja — jednom, offline, s ljudskom provjerom, kroz istu
infrastrukturu iz Faze 2. To je jeftinije od runtime varijante i uz to provjerljivo
prije nego ijedan sudionik zadatak otvori.

**Slučaj A je iznad praga** (468–1 440) i ostaje kandidat za runtime — ali vidi G5:
i ondje najveći dio informacije već postoji na ekranu.

### G1.4 Opcija: gumb `disabled` dok nema ijednog attempta

| dobiva | gubi |
|---|---|
| `error_type` **uvijek postoji** kad je hint dostupan → nestaje cijeli slučaj B i s njim 240-kombinacijski prazan hod | Student koji ne zna **odakle početi** ostaje bez pomoći — a to je najranjiviji trenutak, osobito na evalu bez nadzora |
| `hint_requested` se veže uz **sljedeću** predaju bez dvosmislenosti (postoji točno jedan otvoren pokušaj) | Gumb koji je vidljiv a `disabled` traži razlog (tooltip), inače je kvar |
| Hint uvijek ima što reći o **studentovom radu**, ne samo o zadatku | Gubi se pedagoški najlegitimniji „scaffolding" scenarij — usmjeriti prije prvog pokušaja, umjesto ispravljati poslije |
| Nula LLM poziva na zadacima koje student otvori pa zatvori | — |

⟳ 🔴 **PREPORUKA ISPOD JE POVUČENA** — korisnik je odabrao upravo `disabled` (neaktivan
gumb do prvog netočnog pokušaja). Mehanika je u **§H3**; ovdje ostaje samo trag odbačene
alternative.

~~**Preporuka: NE `disabled`, nego DVA IZVORA.**~~

- **prvi pokušaj (`error_type IS NULL`)** → hint iz **predgenerirane** tablice
  (240 redaka, offline, provjereno). Nula LLM poziva, nula latencije, nula slanja.
- **ponovljeni pokušaj (`error_type` postoji)** → runtime put (LLM ili `hints`
  fallback), i **samo tu** se uopće postavlja pitanje slanja podataka iz §B.1.

Time se G1 kontradikcija ne samo razrješava nego **smanjuje opseg §B.1**: put koji
šalje ikakav podatak vanjskoj usluzi postoji samo za ponovljene pokušaje.

---

## G2 🔴 `expected_query` — izričit odgovor

### G2.1 Jedna rečenica

> **NE. Pod mojom preporukom rješenje zadatka (`expected_query`, `expected_result`)
> NE napušta sustav — ni prema LLM-u, ni prema pregledniku, ni u `agent_messages_log`.**

### G2.2 Gdje je guard i vrijedi li za izravan put

Guard **nije jedan mehanizam** nego tri odvojena mjesta, i to je bitno za odgovor:

| # | mjesto | oblik | vrijedi za gateway → HintAgent? |
|---|---|---|---|
| 1 | [`schemas.py:129-131`](backend/app/api/schemas.py#L129-L131) — `TaskDetailResponse`: *„NAMJERNO bez expected_query / expected_result / sandbox_schema — rješenje se NE izlaže kroz ovaj endpoint"* | Pydantic shema **bez** polja | ❌ **ne** — to je HTTP odgovor, ne FIPA payload |
| 2 | [`routes.py:319-320`](backend/app/api/routes.py#L319-L320) — `_read_task_detail`: *„NAMJERNO gradi dict eksplicitno po poljima"* | ručna konstrukcija dicta | ❌ **ne** — druga funkcija |
| 3 | [`models.py:190-192`](backend/app/db/models.py#L190-L192) — `attempts.detail`: *„NIKAD ne smije sadržavati expected_query ni sadržaj očekivanih redaka"* | **komentar** + disciplina u `evaluation.py` | ❌ **ne** |

🔴 **Nijedan od tri ne vrijedi za izravan put gateway → HintAgent.** HintAgent bi
čitao `Task` red **izravno iz baze** (`session.get(Task, task_id)`), gdje su
`expected_query` i `expected_result` obična polja modela. Nema sloja između njega i
rješenja.

**Empirijski dokaz da je disciplina dosad držala** —
[`faza-4.5-korak-0-inventar.md:74`](docs/faza-4.5-korak-0-inventar.md#L74), sken nad
**svih 552 živa zapisa** `agent_messages_log`a:

| polje | pogodaka |
|---|---|
| `expected_query`, `expected_result`, `expected_output`, `expected_rows`, `first_mismatch` | **0** ✅ |

i zaključak istog dokumenta (`:81`): *„Rješenja zadataka NISU izložena — `expected_query`
nikad ne ulazi u FIPA poruke (poklapa se s guardom iz 4.3 Stage 0b)."*

**Poštena kvalifikacija:** jedan djelić oblika rješenja ipak curi — `wrong_columns`
detail interpolira **imena očekivanih stupaca**
([evaluation.py:199-202](backend/agents/evaluation.py#L199-L202)):

```python
            detail=(
                f"Stupci se razlikuju — dobiveni: {sorted(actual_cols)}, "
```

To su imena stupaca iz `expected_result[0].keys()`, dakle **oblik** rješenja, ne sam
upit. Odluka 4.3 Stage 0b to je svjesno dopustila (pedagoški je nužno reći studentu
koji stupci se traže). **Za HintAgent to znači:** ako se `detail` prosljeđuje u prompt
(varijanta B+ iz §B.1.4), imena očekivanih stupaca idu s njim. To treba **imenovati u
odluci**, ne otkriti poslije.

### G2.3 🔴 Što bi to učinilo dokazivim, a ne stvarom discipline

Danas **ne postoji nijedan test** koji to čuva. Pretraga:

```
$ grep -rn "expected_query\|expected_result" backend/tests/*.py
```

— svih 13 pogodaka koristi `expected_query` kao **ulaz** (`evaluate(task, task.expected_query, …)`),
nijedan ne **tvrdi da ga nema u izlazu**. Jedini dokaz je **jednokratan ručni sken iz
4.5**, nad podacima zatečenim tog dana.

🔴 To je točno razred **#55** („projekt ima instrument za VRIJEDNOSTI, ne za UČINAK")
i **N-18** — pravilo napisano u komentaru, bez ičega što ga izvršava. Sken od 552
zapisa dokazuje **prošlost**, ne **invarijantu**.

**Prijedlog mehanizma (stage 5.1 exit, ne ovaj korak):**

```python
# backend/tests/test_hint_payload_guard.py
def test_hint_payload_ne_sadrzi_rjesenje(db_session):
    """🔴 Za SVAKI aktivan zadatak: payload koji HintAgent gradi ne smije
    sadržavati expected_query ni ijedan redak expected_resulta.

    Ovo NIJE stilska provjera — to je jedini izvršni oblik guarda iz 4.3
    Stage 0b za izravan put gateway → HintAgent (koji zaobilazi i
    TaskDetailResponse i _read_task_detail).
    """
    for task in db_session.scalars(select(Task).where(Task.is_active)):
        payload = build_hint_payload(db_session, user_id=U, task_id=task.id)
        blob = json.dumps(payload, ensure_ascii=False)

        assert task.expected_query not in blob
        # i svaka vrijednost iz očekivanog rezultata, ne samo cijeli JSON
        for row in (task.expected_result or []):
            for value in row.values():
                if isinstance(value, str) and len(value) > 3:
                    assert value not in blob
```

**Zašto ovaj oblik, a ne `assert "expected_query" not in payload`:** provjera imena
ključa hvata samo doslovno prosljeđivanje. Provjera **sadržaja** hvata i slučaj kad
netko ubaci `f"Očekuje se: {task.expected_query}"` u prompt string — što je stvarni
način na koji rješenje procuri u LLM prompt.

**Drugi sloj, za LLM izlaz (ne samo ulaz):** isti test nad `hint_text` prije upisa u
`hints` — LLM koji je vidio shemu može rekonstruirati rješenje i bez da mu ga damo.
Bez toga cache-kroz-`hints` iz §B.5.3 postaje kanal kojim rješenje uđe u bazu i
prikaže se sljedećem studentu.

---

## G3 🔴 Koliko Faza 5 pogoršava #46 — izmjereno

### G3.1 Prolazi li izravan put kroz `log_message`? ✅ DA — i to dvaput

`send_fipa` bezuvjetno logira ([gateway_agent.py:104-110](backend/app/bridge/gateway_agent.py#L104-L110)):

```python
                await self.send(msg)
                gateway.log_message(
                    sender=str(gateway.jid),
                    receiver=to,
                    performative=performative,
                    content=payload,
                    correlation_id=cid,
                )
```

A svaki domenski agent logira i **dolaznu** i **odlaznu** poruku — obrazac
`RecommenderAgent`a, koji je arhitektonski identičan predloženom HintAgentu:
[recommender_agent.py:61](backend/agents/recommender_agent.py#L61) (dolazna REQUEST)
i [recommender_agent.py:124](backend/agents/recommender_agent.py#L124) (odlazna INFORM).

### G3.2 Koliko redaka po hintu i što je u `content` — IZMJERENO

Mjereno nad **stvarnim** prometom `/next-task` puta (isti izravan bridge put koji hint
predlaže), grupirano po `correlation_id`:

```sql
SELECT n_rows, count(*) AS n_cid FROM (
  SELECT correlation_id, count(*) n_rows FROM agent_messages_log
  WHERE receiver LIKE 'recommender%' OR sender LIKE 'recommender%'
  GROUP BY correlation_id) x GROUP BY n_rows ORDER BY n_rows;
```

| redaka po razgovoru | broj razgovora | tumačenje |
|---|---|---|
| 1 | 3 | rubni / prekinuti |
| 2 | 171 | **FSM put** — Coordinatorov `RecommendState` ne logira zahtjev |
| **3** | **397** | **izravan `/next-task` put** — gateway logira + agent logira dolaznu + agent logira odlaznu |

🔴 **Hint = 3 retka po zahtjevu** (dominantni obrazac, 397/571 razgovora).

**Što je u `content` (JSONB), redak po redak:**

| # | sender → receiver | performativ | `content` |
|---|---|---|---|
| 1 | gateway → hint | `request` | **cijeli zahtjevni payload** — `user_id`, `task_id`, i pod varijantom A **`submitted_query`** |
| 2 | gateway → hint | `request` | **isti payload još jednom** (agent logira svoju dolaznu poruku) |
| 3 | hint → gateway | `inform` | **odgovorni payload — `hint_text`**, `source`, `concept`, `remaining` |

Dakle **i upit (varijanta A) i tekst hinta** završe u tablici koja nema `user_id`
kolonu i briše se samo `TRUNCATE`om.

### G3.3 🔴 Ekstrapolacija na eval volumen

Bazna linija iz **#46**: 600 pokušaja (20 sudionika × 30) → **~7 400 zapisa**
(izmjereno 12,3 po pokušaju).

| scenarij | hintova | dodanih zapisa | **prema #46** |
|---|---|---|---|
| hint na ~30 % pokušaja | 180 | 180 × 3 = **540** | **+7,3 %** (7 400 → 7 940) |
| hint na svakom pokušaju | 600 | 600 × 3 = **1 800** | **+24,3 %** (7 400 → 9 200) |
| **samo ponovljeni pokušaji** (preporuka G1.4) | ~120 | **360** | **+4,9 %** |

🔴 **BROJKA ZA STANI-I-JAVI: između +540 i +1 800 zapisa, tj. +7 % do +24 % nad
izmjerenih ~7 400 iz #46.** To ne mijenja **narav** #46 (već je blokator), ali mijenja
**sadržaj**: dosad su neizbrisivi zapisi sadržavali studentove upite; s hintom bi
sadržavali i **tekstove koje je vanjska usluga napisala tom konkretnom studentu**.

### G3.4 🔴 Može li hint promet NE ući u log, uz očuvanu dijagnostiku? ✅ DA — i to je bolji dizajn

`log_message` **nije automatski** — nema middlewarea ni presretača, svaki agent ga
zove ručno ([base.py:64](backend/agents/base.py#L64), 13 poziva u cijelom projektu).
Zato postoje tri razine, ne dvije:

| razina | zapisa/hint | što se gubi |
|---|---|---|
| **(a) puno logiranje** (obrazac Recommendera) | **3** | ništa — ali +7…24 % na #46 s osobnim sadržajem |
| **(b) HintAgent ne zove `log_message`** | **1** (samo gateway) | jednosmjeran trag: vidi se da je zahtjev poslan, ne i što je odgovoreno |
| **(c) 🔴 logiranje s REDIGIRANIM `content`om** | **3** | **ništa što radu treba** — v. dolje |

**Preporuka: (c).** `log_message` prima `content` kao zaseban argument od poruke koja
se šalje — dakle **što se šalje i što se logira mogu se razići bez ijedne izmjene u
`base.py`**:

```python
# HintAgent — šalje pun payload, logira redigiran
await self.send(inform)                     # hint_text ide studentu
self.agent.log_message(
    sender=str(self.agent.jid),
    receiver=to,
    performative=Performative.INFORM,
    content={"task_id": task_id, "source": source, "len": len(hint_text)},  # ← bez teksta
    correlation_id=correlation_id,
)
```

**Što admin viewer (`GET /admin/agent-logs`) zadržava:** `sender`, `receiver`,
`performative`, `correlation_id`, `created_at` — dakle **cijeli FIPA trag razgovora**,
koji je ono što viewer i služi prikazati (`AgentLogItem`,
[schemas.py:260-267](backend/app/api/schemas.py#L260-L267)). Gubi se samo tekstualni
sadržaj poruke.

**Što rad zadržava:** rad dokazuje da postoji **šest agenata koji razmjenjuju
FIPA-ACL poruke s performativima i korelacijom**. Za tu tvrdnju su nosivi upravo
`sender`/`receiver`/`performative`/`correlation_id` — a ne tekst hinta. Redigirani
zapis je **jednako valjan dokaz** višeagentske komunikacije.

**Što se stvarno gubi:** mogućnost da se poslije, iz loga, rekonstruira *koji točno
hint* je student vidio. Ako je to dio istraživačkog pitanja („je li hint pomogao?"),
odgovor daje **G6 tablica** (koja ima `user_id` i briše se CASCADE-om), ne
`agent_messages_log`.

🔴 **Ključna posljedica (c):** redigirani zapis **više nije osobni podatak** — nema
upita, nema teksta pisanog toj osobi, samo tehnički metapodaci razgovora. Time hint
promet **ne proširuje izloženost iz #46**, iako i dalje dodaje redove. Brojka +7…24 %
ostaje, ali ono što u tim redovima stoji prestaje biti ono zbog čega je #46 blokator.

---

## G4 — E1–E3, s brojkama

### G4.1 Lanac timeouta od preglednika do LLM-a

| # | sloj | vrijednost | izvor |
|---|---|---|---|
| 1 | **preglednik / `fetch`** | 🔴 **NEMA** | [`client.ts:35-38`](frontend/src/lib/api/client.ts#L35-L38) — `createClient({baseUrl})`, nula `signal`/`AbortController`; grep na `timeout\|signal\|AbortController` po `lib/api/*.ts` i `hooks/*.ts` daje **nula** pogodaka za konfiguraciju |
| 2 | **TanStack Query** | 🔴 **NEMA** | [`query.ts`](frontend/src/lib/api/query.ts) je samo `unwrap` + `ApiError`; nema `retry`, nema `queryFn` timeouta |
| 3 | **uvicorn** | 🔴 **NEMA request timeout** | `app/main.py` ne postavlja nijedan; uvicornov `timeout_keep_alive=5` odnosi se na **praznu** konekciju, ne na trajanje zahtjeva |
| 4 | **`AgentBridge.wait`** | ✅ **15,0 s** | `asyncio.wait_for(future, timeout)` [`agent_bridge.py:113`](backend/app/bridge/agent_bridge.py#L113), pozvan s `config.GATEWAY_TIMEOUT` [`routes.py:212`](backend/app/api/routes.py#L212); vrijednost [`config.py:63`](backend/app/core/config.py#L63) |
| 5 | Coordinator UPDATE / RECOMMEND | 5,0 / 5,0 s | [`coordinator.py:77-78`](backend/agents/coordinator.py#L77-L78) — **nije na hint putu** |
| 6 | SPADE `CyclicBehaviour.receive` | 10 s poll | npr. [`recommender_agent.py:49`](backend/agents/recommender_agent.py#L49) — poll, ne granica zahtjeva |
| 7 | sandbox `statement_timeout` | 5 s | CLAUDE.md invarijanta — **nije na hint putu** |
| 8 | **Anthropic SDK** | 🔴 **10 min (default)** | SDK default; `AnthropicClient.__init__` ga **ne postavlja** ([api_client.py:51-54](backend/scripts/lib/api_client.py#L51-L54)) |

🔴 **Najmanji je `GATEWAY_TIMEOUT = 15 s` — i to je JEDINA granica u cijelom lancu.**

Dvije posljedice koje treba izgovoriti:

1. **Klijent je neograničen.** Ako granica na sloju 4 iz bilo kojeg razloga ne opali
   (npr. HintAgent odgovori u 14,9 s, pa uvicorn krene serijalizirati odgovor), student
   čeka koliko preglednik odluči. Nema `AbortController`, nema poruke „predugo traje".
   **To je zatečeno stanje, ne posljedica hinta** — ali hint je prva ruta gdje je
   dugotrajnost očekivana, a ne kvar.
2. **SDK default od 10 minuta je 40× iznad jedine granice.** Bez eksplicitnog
   `timeout=` na Anthropic klijentu, LLM poziv može trajati dulje nego cijeli HTTP
   zahtjev — bridge odustane u 15 s, a poziv nastavi trošiti tokene u pozadini, s
   `_pending` redom već očišćenim ([`agent_bridge.py:114-115`](backend/app/bridge/agent_bridge.py#L114-L115)).
   **Zato `HINT_LLM_TIMEOUT` mora biti eksplicitan**, kako §B.5.1 predlaže (8 s), i
   `max_retries=0` (inače 9 poziva × backoff ≫ 15 s).

**Prijedlog E1 (dodatak §B.5.1):** frontend `useHint` dobiva `AbortController` s
**18 s** (iznad servera, da server stigne vratiti strukturiran 504 prije nego klijent
odustane) — jedina izmjena koja lanac zatvara s obje strane.

### G4.2 Rate-limit uzorak u projektu

```
$ grep -rniE "rate.?limit|slowapi|limiter|@cache|lru_cache|functools.cache" backend/ --include=*.py
backend/tests/test_api_client.py:41   def test_rate_limit_triggers_retry_then_succeeds(...)
backend/tests/test_api_client.py:42   from anthropic import RateLimitError as RLE
backend/scripts/lib/api_client.py:8   from anthropic import ..., RateLimitError
backend/scripts/lib/api_client.py:47  # ... ne za API rate-limit (to SDK pokriva)
backend/scripts/lib/api_client.py:92  except RateLimitError as e:
```

🔴 **NE POSTOJI.** Svih pet pogodaka odnosi se na **hvatanje** Anthropicovog
dolaznog rate-limita; nijedan ne **nameće** vlastiti. Nema `slowapi`, nema middlewarea,
nema brojača, nema `lru_cache`. Ovo je prvi put da bi projekt nametao limit.

### G4.3 Cache: gdje, preživljava li restart, realan hit-rate

**Gdje i preživljava li** — nepromijenjeno iz §B.5.3: `hints` tablica (preživljava
restart, shema već postoji) vs. in-memory `dict` (ne preživljava). Preporuka ostaje
tablica.

**Realan hit-rate na eval volumen, uz kardinalnost iz G1** — ovo je novo i mijenja
sliku:

| ključ | kardinalnost | zahtjeva u evalu | očekivani hit-rate |
|---|---|---|---|
| slučaj B (prvi pokušaj), po zadatku | **240** | ~200 | **~0 %** ako se puni runtimeom |
| slučaj B, **predgeneriran** (G1.3) | 240 | ~200 | **100 %** ✅ |
| slučaj A, po **konceptu** (26 × 6 × 3) | **468** | ~120 | **~20 %** |
| slučaj A, po **zadatku** (80 × 6 × 3) | **1 440** | ~120 | **~4 %** |

**Zaključak koji brojke nameću:** runtime cache koji se puni sam **ne stigne se
napuniti** na evalu ovog volumena. 600 pokušaja raspoređenih preko 1 440 (ili čak 468)
ključeva znači da je gotovo svaki zahtjev prvi za svoj ključ. Cache je koristan tek
kod desetostruko većeg volumena ili ponovljenih kohorti.

🔴 **Posljedica: cache-kroz-`hints` NE opravdava se kao mehanizam štednje na evalu.**
Opravdava se samo kao **fallback koji se usput puni** (i za to i dalje vrijedi), a
prava ušteda dolazi iz **predgeneriranja** slučaja B — gdje je hit-rate 100 % po
konstrukciji.

---

## G5 🔴 FALLBACK: 7 redaka duplicira ono što je već na ekranu

### G5.1 `lib/feedback.ts` — mapa u cijelosti

[`feedback.ts:41-53`](frontend/src/lib/feedback.ts#L41-L53):

```ts
/** Glavna hrvatska poruka po error_type (izvor značenja: evaluation.py). */
const ERROR_TEXT: Record<string, string> = {
  syntax_error: "Nisi poslao upit — editor je prazan ili sadržaj nije SQL.",
  execution_error: "Greška u SQL-u — baza nije mogla izvršiti upit.",
  timeout: "Tvoj upit je predugo trajao — pojednostavi ga pa pokušaj ponovno.",
  unsupported_eval:
    "Ovaj tip zadatka se još ne ocjenjuje automatski — rješenje vježbaj kroz Run.",
  empty_result: "Upit nije vratio nijedan redak, a rezultat se očekuje.",
  wrong_columns: "Upit vraća krive stupce.",
  row_mismatch: "Skoro! Stupci su točni, ali redovi nisu.",
}

const FALLBACK_ERROR_TEXT =
  "Ocjenjivanje nije uspjelo — pokušaj ponovno predati rješenje."
```

Uz to `detailPresentation` ([feedback.ts:79-89](frontend/src/lib/feedback.ts#L79-L89))
propušta i **pedagoški `detail`** kao čitljiv tekst za `wrong_columns` (nabraja
stupce), `empty_result` (broj redova), `syntax_error` i `unsupported_eval`.

**Kada je taj tekst na ekranu:** `submitSlot === "feedback"` renderira `FeedbackPanel`
s `lastAttempt` ([TaskPage.tsx:462-471](frontend/src/pages/TaskPage.tsx#L462-L471)).
Hint gumb bi bio u akcijskom redu **iznad** tog panela. Student koji klikne „Zatraži
hint" nakon neuspjele predaje **gleda `ERROR_TEXT` dok kliká.**

### G5.2 🔴 Bi li student dobio parafrazu poruke koju upravo čita? — po tipu

| `error_type` | `ERROR_TEXT` (već na ekranu) | moj prijedlog iz §B.3.4 | parafraza? |
|---|---|---|---|
| `syntax_error` | „Nisi poslao upit — editor je prazan ili sadržaj nije SQL." | „upit je prazan ili neprepoznatljiv — provjeri je li editor prazan" | 🔴 **DA** |
| `execution_error` | „Greška u SQL-u — baza nije mogla izvršiti upit." | „baza je odbila upit; poruka o grešci je u panelu ispod — počni od nje" | 🔴 **DA** — i gore: upućuje na panel koji je već otvoren |
| `timeout` | „Tvoj upit je predugo trajao — pojednostavi ga pa pokušaj ponovno." | „predugo trajao — provjeri ima li nenamjeran križni spoj" | 🟡 **uglavnom** (dodaje samo „križni spoj") |
| `unsupported_eval` | „Ovaj tip zadatka se još ne ocjenjuje automatski — rješenje vježbaj kroz Run." | „ovaj tip zadatka sustav još ne ocjenjuje automatski" | 🔴 **DA — doslovno, i kraće od originala** |
| `empty_result` | „Upit nije vratio nijedan redak, a rezultat se očekuje." (+ detail: broj očekivanih redova) | „nije vratio nijedan redak — provjeri uvjete u `WHERE`" | 🟡 **uglavnom** (dodaje samo „`WHERE`") |
| `wrong_columns` | „Upit vraća krive stupce." (+ detail **nabraja** dobivene i očekivane stupce) | „usporedi popis u `SELECT` s tekstom zadatka" | 🔴 **DA** — i **slabije**, jer detail već imenuje stupce |
| `row_mismatch` | „Skoro! Stupci su točni, ali redovi nisu." | „provjeri filtriranje, spajanje i grupiranje" | 🟡 **uglavnom** |

🔴 **STANI-I-JAVI (G5.2): DA — 4 od 7 su čista parafraza, preostala 3 dodaju po
jednu riječ.** Prijedlog od 7 generičkih redaka iz §B.3.4 **ne prolazi**. Student bi
kliknuo gumb, pričekao, i dobio prepričanu rečenicu koja mu stoji 200 px niže na
istom ekranu. To bi bio **gori** ishod od gumba koji ne postoji, jer troši i klik i
povjerenje.

**Metodološki:** ovo je isti razred kao **#57** — instrument (moj prijedlog fallbacka)
kalibriran prema zatečenom stanju (taksonomiji `error_type`) potvrđuje zatečeno
stanje (poruku koja je iz iste taksonomije već izvedena). Provjeru je trebalo napraviti
u §B.3.4, ne u §G.

### G5.3 Pokrivenost po PAROVIMA — izvedeno iz baze

```sql
SELECT c.code, count(*) AS n_tasks
FROM concepts c JOIN task_concepts tc ON tc.concept_id=c.id AND tc.is_primary
JOIN tasks t ON t.id=tc.task_id AND t.is_active
GROUP BY c.code ORDER BY n_tasks DESC;
```

**26 koncepata nosi 80 aktivnih zadataka** (raspodjela: `group_by` 5,
`multi_table_join` 5, zatim šest po 4, deset po 3, osam po 2).

Od 6 dosežnih `error_type` vrijednosti (G1.3), **koncept-ovisne su 4**:

| `error_type` | koncept-ovisan? | zašto |
|---|---|---|
| `empty_result` | ✅ | *zašto* je prazno ovisi o konceptu (WHERE vs. HAVING vs. JOIN) |
| `wrong_columns` | ✅ | koji stupci nedostaju ovisi o konceptu (agregat, alias, projekcija) |
| `row_mismatch` | ✅ | duplikati iz JOIN-a ≠ krivi GROUP BY ≠ krivi ORDER BY |
| `execution_error` | ✅ | tipične PG greške razlikuju se po konstruktu |
| `syntax_error` | ❌ | prazan editor — nema veze s konceptom |
| `timeout` | 🟡 | relevantan samo za spojeve (`cross_join`, `self_join`, `multi_table_join`) |

**Puna pokrivenost po parovima: 26 × 4 = 104 retka** (+3 za `timeout` na spojnim
konceptima = **107**).

### G5.4 🔴 Revidiran minimum za 5.0, s eksplicitnim kriterijem

**Kriterij prihvaćanja (novi, obvezujući):**

> Redak u `hints` prolazi **samo ako nosi informaciju koje u
> `frontend/src/lib/feedback.ts` NEMA.** Konkretno: mora imenovati **SQL konstrukt ili
> pravilo vezano uz koncept**, ne prepričati klasifikaciju greške. Provjera je
> mehanička i ide u test: `hint_text` ne smije biti parafraza `ERROR_TEXT[error_type]`,
> i **mora sadržavati barem jedan pojam specifičan za koncept**.

Primjer koji **prolazi** (`empty_result` × `left_join`):

> „`LEFT JOIN` zadržava retke lijeve tablice i kad desna nema para. Ako ti je rezultat
> prazan, provjeri je li uvjet u `WHERE` nad stupcem desne tablice poništio upravo te
> retke — time `LEFT JOIN` tiho postaje `INNER JOIN`."

Primjer koji **pada** (`empty_result`, generički): „Upit nije vratio nijedan redak —
provjeri uvjete u `WHERE`." → parafraza `ERROR_TEXT.empty_result`.

**Revidiran minimalni seed za 5.0** *(⟳ brojka podignuta u §H3.5 — v. dolje)*:

| sloj | redaka | napomena |
|---|---|---|
| ~~**koncept-parovi**, top 8 koncepata × 4~~ | ~~32~~ | ⟳ **nedovoljno** — pod djelomičnom pokrivenošću dostupnost hinta ovisi o tome radi li LLM, pa postaje nekontrolirana varijabla (§H3.5) |
| ✅ **koncept-parovi, SVIH 26 koncepata × 4 koncept-ovisna `error_type`** | **104** | ⟳ **novi floor za 5.0** (§H3.5, razrješenje (c)); +3 za `timeout` na spojnim konceptima = 107 kao puni cilj |
| ~~generički sloj (`concept_id IS NULL`)~~ | ~~7~~ | 🔴 **UKINUT** — pada na kriteriju G5.4 |

⟳ **Prioritet unutar 104:** `row_mismatch` × koncept ide **prvi** — §H3.2 pokazuje da je
djelomičan pokušaj pedagoški najvrjedniji slučaj za savjet, ne jedan od četiri
ravnopravna.

🔴 **Posljedica ukidanja generičkog sloja:** kad **nema** koncept-parnog retka i LLM
je nedostupan, ruta vraća **503 `hint_unavailable`** i UI gumb prikazuje kao
`unavailable` — umjesto da servira parafrazu. **To je bolji ishod:** ne trošiti
studentov klik na rečenicu koju već čita.

Puna pokrivenost (104–107 redaka) ostaje cilj, ali se puni **iz upotrebe** — koncepti
koji se u evalu pokažu kao usko grlo dobivaju retke prvi.

---

## G6 — INSTRUMENT: `hint_requests` tablica

Prijedlog na ocjenu (nije implementiran). ⟳ **Shema ispod je prvotna; konačna je u
§H3.6** (dodani `after_attempt_id`, `hint_id`, `hint_text`; `error_type` postao
`NOT NULL`).

```sql
hint_requests(
  id          serial PRIMARY KEY,
  user_id     integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  task_id     integer NOT NULL REFERENCES tasks(id),
  source      varchar(16) NOT NULL,      -- 'llm' | 'fallback'
  error_type  varchar(100),              -- ⟳ postaje NOT NULL (H3.6)
  created_at  timestamptz NOT NULL DEFAULT now()
)
```

### G6.1 Rješava li CASCADE per-user brisanje? ✅ DA — i to je glavna vrijednost

**Za razliku od `agent_messages_log`**, koji je jezgra #46 upravo zato što **nema
`user_id` ni FK na `users`** ([models.py:394-409](backend/app/db/models.py#L394-L409)
— 7 stupaca, nijedan ne referencira korisnika), ova tablica ga ima s
`ON DELETE CASCADE`.

**Konkretno:** `purge_demo_users.py` briše 9 tablica — *„3 eksplicitno + 5 CASCADE +
`users`"* (#46). Brisanje `users` reda povlači CASCADE-om sve što na njega upućuje,
pa `hint_requests` **ne treba ni dodavati u skriptu** — pokriva se automatski, kao i
`streaks`, `skill_mastery` i ostale CASCADE tablice. Isti obrazac koji već koristi
`RecommendationLog` ([models.py:381-383](backend/app/db/models.py#L381-L383)).

✅ **Podatak o traženju hinta postaje brisiv po osobi. `agent_messages_log` nije i
ostaje nije** — pa se G3.4(c) (redigirani log) i G6 **nadopunjuju**: puni podatak
živi ondje gdje se može obrisati, tehnički trag ondje gdje se ne može.

### G6.2 Ostaje li `hint_requested` u `AttemptRequest` potreban?

**Što svaka od dvije stvari mjeri:**

| | mjeri |
|---|---|
| `hint_requests` redak | **događaj**: „student je u trenutku T zatražio hint na zadatku X, izvor je bio Y" |
| `attempts.hint_requested` | **atribuciju ishoda**: „OVA predaja je učinjena nakon što je hint viđen" |

Formalno: zastavica je **izvediva** iz tablice temporalnim joinom (postoji li
`hint_requests` redak istog `(user_id, task_id)` između prethodne i ove predaje).
Dakle **nije nužna**.

🔴 **I to je bitno, jer izvedivost uklanja izmjenu FIPA protokola.** §B.4.1 traži da
zastavica putuje `AttemptRequest` → `submit-attempt` → **`evaluate-query` payload** →
`persist_attempt`. Ako se zastavica izvodi iz tablice:

| dodirnuto pod §B.4.1 (zastavica) | dodirnuto uz `hint_requests` |
|---|---|
| `AttemptRequest` shema | — |
| `persist_attempt` potpis | — |
| 🔴 **`evaluate-query` FIPA payload (+1 polje)** | — |
| `schema.d.ts`: `AttemptRequest` | — |
| frontend drži per-task stanje „hint zatražen" | — |
| — | **jedna Alembic migracija** |

**Trampa je jasna:** jedna migracija **umjesto** izmjene FIPA protokola i dodira
`persistence.py` — dakle **umjesto dodira eval-verificiranog puta**. Uz projektnu
poziciju o zamrznutom backendu i eval-verificiranom putu, **migracija je jeftinija i
sigurnija**.

🔴 **Preporuka: uzeti tablicu, `hint_requested` OSTAVITI hardkodiran na `False`.**
Kolona ostaje ono što je i bila — rezervirano mjesto iz Faze 1 — a
`export_eval_data.py:87` je i dalje izvozi (uvijek `false`), što treba **zapisati u
eval runbook** da nitko ne zaključi da hintovi nisu korišteni. Atribucija za rad
izvodi se iz `hint_requests` joinom, i to eksplicitnim SQL-om u izvoznoj skripti, gdje
je vidljiva i provjerljiva.

**Poštena mana ovog izbora:** temporalni join ima rubne slučajeve (hint zatražen pa
zadatak napušten; dva hinta između dvije predaje; hint nakon zadnje predaje). Zastavica
ih nema. **Ali** ti su rubni slučajevi *podaci*, ne šum — `hint_requests` ih čuva sve,
dok bi zastavica hint bez predaje **izgubila u cijelosti**. Tablica je bogatiji
instrument, ne samo sigurniji.

### G6.3 Što se mijenja u `schema.d.ts` i treba li migracija

**Migracija: DA** — jedna Alembic revizija, jedna nova tablica. Posljedica:
`test_db_schema.py:23` nabraja 16 tablica → postaje **17**, i to je jedini test koji
puca. 🔴 Po CLAUDE.md, izmjena sheme traži pitanje prije izvedbe.

**`schema.d.ts` — revidiran popis (uži od §B.4.3).** ⟳ **Konačan popis je u §H3.4** —
dodan je `TaskDetailResponse.last_attempt_error_type` (jedina stavka koja je ovaj popis
proširila).

| shema | izmjena |
|---|---|
| `components["schemas"]["MeResponse"]` | **+ `hints_enabled: boolean`** |
| ⟳ `components["schemas"]["TaskDetailResponse"]` | **+ `last_attempt_error_type?: string \| null`** (H3.4) |
| `components["schemas"]["HintRequest"]` | **nova** — `task_id: number` (+ `submitted_query?` samo pod varijantom A) |
| `components["schemas"]["HintResponse"]` | **nova** — `hint_text: string` · `source: string` · `concept?: string \| null` · `remaining?: number \| null` |
| `paths["/hint"]["post"]` | **nov** |
| ~~`AttemptRequest.hint_requested`~~ | 🔴 **UKLONJENO iz plana** — nije potrebno (G6.2) |

`hint_requests` je **interna** tablica; ne izlaže se rutom, pa u `schema.d.ts` ne ulazi.

---

## G7 — N-20: zamrzni natpis + test umjesto responzivnog skrivanja

Prihvaćam prigovor. `lg` je 1024 px, problem je 768–~790 px: responzivno skrivanje
riječi na **234 px** raspona zbog **22 px** problema jest nesrazmjerno, a gumb koji
piše samo „hint" je engleska imenica bez glagola — u sučelju koje je inače na
hrvatskom i glagolsko („Predaj", „Pokreni", „Zatraži").

**Revidirana preporuka: natpis se zamrzava na „Zatraži hint", a popravak je TEST.**

### G7.1 Playwright assertion

Natpis je **vrijednost koja trenutno prolazi**; test je **popravak**, jer hvata svaku
buduću promjenu natpisa, ikone, `gap`a, `px`a ili širine `Kbd` čipa.

```ts
// frontend/e2e/smoke.spec.ts (dodatak — Faza 5.2)
//
// 🔴 NALAZ N-20: na 768 px akcijski red ima 2,47 px slacka. Svaki natpis duži
// od „Zatraži hint" (119 px) wrapa red 44 → 94–100 px i produžuje karticu za
// 50–56 px, čime FeedbackPanel pada niže. Natpis NIJE invarijanta — invarijanta
// je da red stane u JEDAN redak; natpis je samo vrijednost koja to trenutno
// zadovoljava.
test("N-20: akcijski red ne wrapa na 768 px", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 })
  await page.goto(`/task/${TASK_ID}`)

  const editor = page.getByTestId("task-editor-box")
  const row = page.getByTestId("task-actions")

  await expect(editor).toBeVisible()

  // Sidro mjerenja: editor je h-[420px] ispod xl. Ako se ovo promijeni,
  // brojke iz N-20 više ne vrijede i mjerenje treba ponoviti.
  expect((await editor.boundingBox())!.height).toBe(420)

  // 🔴 POPRAVAK: h-11 = 44 px. Wrap daje ≥94 px — pada glasno, ne tiho.
  expect((await row.boundingBox())!.height).toBe(44)
})
```

Traži dva `data-testid` atributa
([TaskPage.tsx:408](frontend/src/pages/TaskPage.tsx#L408) i
[:417](frontend/src/pages/TaskPage.tsx#L417)) — jedina izmjena koju test nameće
produkcijskom kodu, i to nevidljiva.

**Zašto `toBe(44)`, a ne `toBeLessThan(50)`:** wrap na 768 px daje 94–100 px, pa bi i
labav prag prošao. Ali `toBe` hvata i suprotan smjer — netko tko poveća visinu gumba
(`h-11` → `h-12`) mijenja isti proračun, a to labav prag propušta.

**Ograničenje testa, pošteno:** smoke suite piše u **živu** `tutor_main`
([playwright.config.ts](frontend/playwright.config.ts)) i po pravilu #40 se ne pokreće
tijekom evaluacijske sesije. Test je gate **prije** evala, ne nadzor **tijekom** njega.

### G7.2 ✅ Potvrđeno: rate-limit brojač NE ide u label

Izmjereno u tri `gap` varijante:

| viewport | `gap` | „Zatraži hint (1/3)" (148 px) | red | kartica |
|---|---|---|---|---|
| 768 | `gap-3` (12 px) | slack **−26,53 px** | **100 px** | **596 px** 🔴 |
| 768 | `gap-2` (8 px) | slack **−22,53 px** | **96 px** | **592 px** 🔴 |
| 768 | `gap-1.5` (6 px) | slack **−20,53 px** | **94 px** | **590 px** 🔴 |
| 780 | `gap-2` | slack **−10,53 px** | **96 px** | **592 px** 🔴 |
| 800 | `gap-3` | slack +5,47 px | 44 px | 540 px ✅ |

🔴 **Brojač u natpisu wrapa pod svakom `gap` varijantom sve do ~790 px. Ne ide u label.**

**Prijedlog gdje ide — po stanju:**

| stanje | mjesto brojača | obrazloženje |
|---|---|---|
| `idle`, ima preostalo | **nigdje** | brojač koji nije relevantan je šum; student koji nije potrošio nijedan hint ne treba znati da postoji limit |
| `idle`, **zadnji** preostali (`remaining === 1`) | `title` atribut gumba (tooltip) | jedina točka gdje informacija mijenja odluku |
| `rate-limited` | gumb `disabled` + **razlog ispod gumba**, u istom slotu gdje ide i tekst hinta | slot već postoji u dizajnu (§D.3), pa nema nove strukture; `disabled` bez razloga je kvar |

Konkretno za `rate-limited`: gumb `disabled`, a u hint slotu neutralni redak
„Iskoristio si sve savjete za ovaj sat. Pokušaj ponovno kasnije." Slot je **ispod**
akcijskog reda, pa na širinu reda ne utječe — mjerenje iz G7.2 ga ne dira.

### G7.3 Koliko slacka donosi `gap-3` → `gap-2` u tom pojasu — IZMJERENO

| viewport | `gap-3` (12 px) | `gap-2` (8 px) | `gap-1.5` (6 px) |
|---|---|---|---|
| **768** | **2,47 px** | **6,47 px** *(+4,00)* | **8,47 px** *(+6,00)* |
| 780 | 14,47 px | 18,47 px *(+4,00)* | 20,47 px *(+6,00)* |
| 800 | 34,47 px | 38,47 px *(+4,00)* | 40,47 px *(+6,00)* |

Dobitak je **točno razlika u `gap`u** (12 → 8 = +4 px; 12 → 6 = +6 px) — očekivano,
jer je u redu samo jedan razmak.

🔴 **Smanjenje `gap`a NIJE popravak.** +4 px protiv manjka od 15–27 px za bilo koji
duži natpis. Jedini natpis koji `gap-2` spašava je „Zatraži pomoć" i to tek **od
780 px naviše** (slack 0,47 px — što je unutar šuma zaokruživanja, dakle ne računa se
kao prolaz). Uz to `gap-3` je vrijednost iz dizajn sustava koja se pojavljuje po
cijelom sučelju; mijenjati je zbog 4 px u 22 px pojasu znači uvesti nekonzistentnost
skupu od problema.

**Presuda G7:** natpis se zamrzava na **„Zatraži hint"**, `gap-3` ostaje, popravak je
test iz G7.1. Responzivno skrivanje riječi iz §B.6.3 se **povlači**.

---

# H — TRI ZATVARANJA PRIJE 5.0

> **Polazi od odluke korisnika (donesena, ne raspravlja se):** hint je dostupan **tek
> nakon što na tom zadatku postoji barem jedan netočan pokušaj**; prije toga gumb
> postoji ali je neaktivan. **§G1.3 i §G1.4 su time povučeni** — v. oznaku ondje.

---

## H1 🔴 G3.4(c) + G6 zajedno gube tekst hinta

### H1.1 Kontradikcija — POTVRĐENA

§G3.4 tvrdi: *„Ako je to dio istraživačkog pitanja („je li hint pomogao?"), odgovor daje
**G6 tablica** (koja ima `user_id` i briše se CASCADE-om), ne `agent_messages_log`."*

Shema iz §G6:

```sql
hint_requests(id, user_id, task_id, source, error_type, created_at)
```

**Nema `hint_text`. Nema FK na `hints`.** Ako se uz to prihvati G3.4(c) (redigiran
`content` u logu), tekst hinta **ne postoji nigdje** — ni u logu, ni u tablici, ni u
`attempts`. Tvrdnja je bila neutemeljena vlastitom shemom; G3.4 je preusmjerio na
instrument koji taj podatak ne nosi.

### H1.2 🔴 Je li tekst hinta osobni podatak — presuda

**Razlika koju treba izgovoriti:**

| | `submitted_query` | `hint_text` |
|---|---|---|
| autor | **student** | **sustav** (seedani tekst ili LLM) |
| sadržaj | studentov vlastiti intelektualni rad | rečenica o SQL konstruktu, iz omeđenog skupa |
| jedinstvenost | jedinstven po osobi | **dijeljen** — isti tekst dobiju svi s istim `(error_type, concept)` |
| što otkriva sam po sebi | kako ta osoba razmišlja | ništa o osobi |

> 🔴 **PRESUDA: sam tekst hinta NIJE osobni podatak. Veza `user_id → hint_text` JEST.**

Tekst „`LEFT JOIN` zadržava retke lijeve tablice…" ne govori ništa ni o kome. Zapis
„student 7 je vidio taj tekst" govori da je student 7 pogriješio na `left_join` s
`empty_result` — a to je **izvedeni podatak o osobi** (zaključak o njezinu znanju), i
kao takav osobni. Ali **isti zaključak već nosi `attempts.error_type` + `task_id`**,
koji su u bazi od Faze 1 i koje se ionako izvozi za rad. `hint_text` u toj vezi **ne
dodaje novu kategoriju izloženosti** — dodaje čitljivost istog zaključka.

**Što to znači za #46 — i to je ključno:** pohrana teksta u `hint_requests` **ne
pogoršava #46, nego ga ublažava.** Danas bi odgovor na „koji hint je student vidio"
živio u `agent_messages_log`u, koji nema `user_id` i briše se samo `TRUNCATE`om. Ovo
ga premješta u tablicu s `ON DELETE CASCADE`. **Isti podatak, iz neizbrisive tablice u
izbrisivu.** Uz G3.4(c) to daje čistu podjelu:

| gdje | što | brisivo po osobi? |
|---|---|---|
| `agent_messages_log` | tehnički FIPA trag (tko, kome, performativ, cid) — **redigiran** | ❌ ne (i ne mora — nije osobni podatak) |
| `hint_requests` | pun sadržaj vezan uz osobu | ✅ **da**, CASCADE |

**Ocjena proširenja: ✅ PRIHVATITI, uz obje kolone.**

```sql
hint_id    integer NULL REFERENCES hints(id),   -- NULL kad je izvor LLM
hint_text  text NOT NULL                        -- SNAPSHOT onoga što je student vidio
```

**Zašto obje, a ne samo FK:**

- `hint_id` daje **analitičku grupu** („koliko je puta serviran baš taj redak") i
  provjerljivu vezu na kurirani korpus.
- `hint_text` je **snimka**. FK bi vraćao *tekuću* vrijednost `hints.hint_text`, a rad
  treba ono što je student **vidio u tom trenutku**. Ako se redak ikad ispravi (a
  hoće — 5.0 seeda 104 retka koji će se dotjerivati), FK tiho prepisuje povijest.
  Isti razlog zbog kojeg `xp_log` nosi `delta` umjesto da je izvodi iz tekuće formule.
- `hint_id` mora biti `NULL`-abilan jer LLM izlaz **nema** redak u `hints` — v. **H2**,
  gdje se `hints` proglašava read-only u runtimeu.

### H1.3 Što se mijenja

**Migracija** — ista jedna Alembic revizija iz §G6 (tablica se tek stvara, nema
naknadnog `ALTER`a):

```
+ hint_id    integer NULL     REFERENCES hints(id)
+ hint_text  text    NOT NULL
```

FK na `hints` **bez** `ON DELETE CASCADE` — brisanje kuriranog retka ne smije brisati
zapis o tome da ga je student vidio. `ON DELETE SET NULL` je ispravan izbor (`hint_text`
snimka preživi). Tablica i dalje 17., `test_db_schema.py:23` i dalje jedini test koji
puca.

**`export_eval_data.py`** — dodaje se peti upit u `QUERIES`
([export_eval_data.py:81](backend/scripts/export_eval_data.py#L81)), po uzoru na
postojeće (pseudonimizacija `user_id`, `source_id` uz `task_id` zbog **#21** —
`task_id` je nestabilan preko reseeda):

```python
    "hint_requests": """
        SELECT hr.id, hr.user_id, hr.task_id, t.source_id,
               hr.after_attempt_id, hr.error_type, hr.source,
               hr.hint_id, hr.hint_text, hr.created_at
        FROM hint_requests hr
        JOIN tasks t ON t.id = hr.task_id
        ORDER BY hr.user_id, hr.created_at, hr.id
    """,
```

🔴 **`hint_text` u izvozu je odluka za sebe.** Izvoz ide u rad; tekst nije osobni
podatak (H1.2), ali njegova veza s pseudonimom jest. Preporuka: **izvoziti**, jer je
pseudonimiziran kao i sve ostalo, a bez njega se ne može ni provjeriti je li hint bio
relevantan. Ako se odbije — izvoziti samo `hint_id` + `md5(hint_text)`, čime se grupe
i dalje broje.

**Eval runbook** — dvije rečenice:

1. *„`attempts.hint_requested` je uvijek `false` (G6.2). Traženje hinta se čita
   **isključivo** iz `hint_requests.csv`; `false` u `attempts` **ne** znači da hint nije
   korišten."*
2. *„`hint_requests.hint_text` je snimka teksta u trenutku prikaza. `hints.hint_text`
   se u međuvremenu mogao promijeniti — za analizu vrijedi snimka, ne tekuća
   vrijednost."*

### H1.4 Ako se prijedlog odbije

Bez pohranjenog teksta rad može tvrditi **točno ovo**, i ništa više:

> „Sudionici su zatražili N savjeta na M zadataka. Savjet je tražen nakon pokušaja
> klasificiranih kao `<raspodjela error_type>`, najčešće na konceptima `<popis>`.
> Od pokušaja koji su neposredno slijedili traženje savjeta, X % je bilo točno, prema
> Y % kod pokušaja bez prethodnog savjeta."

**Je li dovoljno za odluku 6 (hint kao deskriptivan podatak, ne mjerena varijabla)?**
✅ **Da — ali samo za deskriptivnu ulogu.** Rečenica nosi učestalost, raspodjelu po
konceptu i grubu asocijaciju s ishodom. To je dovoljno da se hint opiše kao pojava.

🔴 **Nije dovoljno ni za jedno od sljedećeg**, i to treba izgovoriti unaprijed:
- razlikovati **je li hint pomogao** od **je li tekst bio dobar** (bez teksta, svaki
  neuspjeh se pripisuje mehanizmu, ne sadržaju);
- razlikovati **LLM** od **fallback** kvalitete — `source` kaže odakle, ne što je pisalo;
- odgovoriti recenzentu na *„navedite primjer savjeta koji je sustav dao"* — na to bez
  teksta nema odgovora, a to je pitanje koje se na obrani postavlja.

Trošak pohrane je jedan `text` stupac u tablici koja ionako nastaje. **Preporuka:
prihvatiti.**

---

## H2 🔴 LLM izlaz u `hints` nema guard u exitu

### H2.1 Postoji li upisni put u mom prijedlogu? ✅ DA — i točno je gdje kažete

Prigovor stoji. Tri mjesta ga zajedno uspostavljaju:

| gdje | tvrdnja |
|---|---|
| §B.5.3 | *„LLM-generiran hint koji prođe validator upisuje se kao redak; sljedeći student s istim `(error_type, concept)` dobiva ga **iz baze, bez LLM poziva**"* |
| §C „Što se NE gradi" | *„`hints` ostaje fallback koji se usput puni"* |
| §G2.3 | *„LLM koji je vidio shemu može rekonstruirati rješenje… Bez toga cache-kroz-`hints` postaje kanal kojim rješenje uđe u bazu i prikaže se sljedećem studentu."* |

Upis bi bio u `HintAgent`u, neposredno nakon uspješnog LLM poziva, prije slanja
`inform`a. **A exit 5.1 testira `build_hint_payload` — dakle ULAZ.** Guarda nad izlazom
nema ni u jednom exit kriteriju. Uz to kriterij kvalitete §G5.4 primjenjuje se u **5.0**
na seedane retke i **ne dodiruje** retke koje LLM doda tijekom evala. Dakle: korpus koji
je u 5.0 kuriran, tijekom evala se puni nekuriranim sadržajem — i servira ga sljedećem
studentu.

Za tri odvojena mjesta koja izgovaraju isti mehanizam a nijedan exit ga ne pokriva —
to je **#55 u čistom obliku**: pravilo postoji kao tekst, ne kao izvršna provjera.

### H2.2 🔴 (a) READ-ONLY vs (b) upis uz runtime provjeru

| | **(a) `hints` READ-ONLY u runtimeu** | **(b) upis uz provjeru prije `INSERT`a** |
|---|---|---|
| **što se gubi** | cache se ne puni sam → svaki runtime hint je LLM poziv | ništa u funkciji |
| **koliko košta** | v. H2.3 — **manje od 6 centi na cijeli eval** | validator koji mora izvršiti **i** §G2.3 (nema rješenja) **i** §G5.4 (nije parafraza + sadrži pojam koncepta) |
| **dokazivo testom?** | ✅ **DA, ishodom**: pokreni 10 hintova, `SELECT count(*) FROM hints` mora biti **nepromijenjen**. Mjeri **posljedicu**, ne oblik koda | 🔴 **NE u dijelu koji je bitan.** Validator je unit-testabilan, ali „korpus ostaje čist kroz cijeli eval" je **runtime svojstvo** — dokazuje se tek nakon evala, kad je kasno |
| **način pada** | LLM padne → fallback iz kuriranog korpusa. Korpus se ne može pokvariti jer se ne piše | validator propusti jedan redak → **trajno** u bazi, servira se svim sljedećim studentima, i nitko ne primijeti jer nema tko čitati 100+ redaka |
| **§G5.4 kriterij** | vrijedi za **cijeli** korpus, jer je cijeli korpus kuriran | vrijedi za 104 seedana retka; za ostatak ovisi o heuristici koja mora prosuditi „sadrži li pojam specifičan za koncept" — semantička provjera u `if`u |

🔴 **STANI-I-JAVI (H2.2) — PREPORUKA: (a) READ-ONLY.**

Odlučuje **asimetrija posljedice**, ne cijena. (b) štedi centе, a riskira da tekst koji
sadrži rješenje ili je besmislen uđe u korpus i posluži se **svim** sljedećim studentima
tijekom evala bez nadzora. (a) gubi uštedu koja je, izmjereno, zanemariva.

Sekundarno, ali ne nevažno: pod (a) **`hints` postaje čisto kurirani artefakt** —
skup koji je čovjek napisao i pregledao, i koji se u radu može navesti u prilogu. Pod
(b) je to hibrid čije podrijetlo po retku više nitko ne zna.

**Provediv oblik (a):** ne oslanjati se na disciplinu. HintAgent otvara sesiju za
`hints` u read-only namjeri, a exit test to **mjeri ishodom** (broj redaka prije i
poslije 10 hintova). Jači oblik, ako se poželi: zasebna PG rola sa `SELECT`-only na
`hints` — isti obrazac koji sandbox već koristi (`sandbox_readonly`), pa nije novi
koncept u projektu.

### H2.3 Koliko cache uopće vrijedi — s brojkama iz §G4.3

Uz odluku korisnika (hint tek nakon netočnog pokušaja), runtime hintova na evalu je
**~120** (§G3.3). Hit-rate iz §G4.3 je **4–20 %** (468–1 440 ključeva, 120 zahtjeva):

| hit-rate | ušteđenih LLM poziva | ušteda (Haiku, 0,0024 $/hint) |
|---|---|---|
| 4 % | 5 | **0,012 $** |
| 20 % | 24 | **0,058 $** |

> 🔴 **Cijeli cache vrijedi između jednog i šest centi na eval volumen.**

Za tih šest centi (b) traži: validator koji izvršava dva netrivijalna kriterija,
njegove testove, i trajni rizik da nekurirani tekst uđe u korpus. **Trampa se ne brani.**

### H2.4 Predložena izmjena exit kriterija 5.1 i retka „Što se NE gradi"

**Exit 5.1 — dodaje se:**

> ⟳ 🔴 **`hints` je read-only u runtimeu — dokazano ishodom:** `SELECT count(*) FROM hints`
> identičan prije i poslije serije od 10 hintova (uključujući ≥3 koja su prošla kroz LLM).
> Nula `INSERT`/`UPDATE` nad `hints` izvan seed skripte.

**„Što se NE gradi u Fazi 5" — redak se mijenja iz:**

> ~~Runtime cache kao mehanizam štednje — mjerenjem odbačen za eval volumen (§G4.3,
> hit-rate ~4–20 %); `hints` ostaje fallback koji se usput puni, ne optimizacija~~

**u:**

> ⟳ 🔴 **Runtime upis u `hints` — u cijelosti.** Tablica je **read-only u runtimeu** i
> mijenja se isključivo seed skriptom. Cache-kroz-`hints` iz §B.5.3 se **povlači**:
> izmjereno vrijedi 0,01–0,06 $ na eval volumen (§H2.3), a otvara kanal kojim
> nekuriran LLM tekst — moguće s rekonstruiranim rješenjem (§G2.3) — ulazi u korpus i
> servira se svim sljedećim studentima. `hints` je **kurirani fallback**, ne cache.

---

## H3 🔴 MEHANIKA OTKLJUČAVANJA

### H3.1 🔴 Uvjet u SQL-u — jamči li klasifikaciju?

**Čitanje `evaluation.py`:** svih **7** izlaza s `is_correct=False` postavlja
ne-`None` `error_type` (retci 84/86, 98/100, 126/128, 150/152, 180/182, 194/196,
207/209), a **oba** izlaza s `error_type=None` imaju `is_correct=True` (142/144,
165/167). Invarijanta drži u kodu.

**Mjerenje nad živom bazom:**

```sql
SELECT is_correct, (error_type IS NULL) AS et_null, count(*) FROM attempts GROUP BY 1,2;
 is_correct | et_null | count
------------+---------+-------
 f          | f       |    13
 t          | t       |    21
```

🔴 **Nula protuprimjera.** Nijedan `is_correct = false` uz `error_type IS NULL`.

**I treći dokaz — jedinstvenost pisca:**

```
$ grep -rn "Attempt(" backend/ --include=*.py | grep -v tests
backend/app/db/models.py:171:class Attempt(Base):
backend/agents/persistence.py:65:        row = Attempt(
```

`persist_attempt` je **jedini** proizvodni pisac `attempts` redova, a on prepisuje
`outcome.error_type` doslovno ([persistence.py:70](backend/agents/persistence.py#L70)).
Nema druge putanje.

> ✅ **Uvjet `is_correct = false` JAMČI `error_type IS NOT NULL`.** Ne treba se
> pooštravati. **Nema STANI-I-JAVI za H3.1.**

🟡 **Ali s jednom kvalifikacijom koju vrijedi zapisati:** to je **invarijanta koda,
ne sheme**. `attempts.error_type` je `nullable=True`
([models.py:188](backend/app/db/models.py#L188)) i nema `CHECK` ograničenja. Ako
`hint_requests.error_type` bude `NOT NULL` (H3.6), on se oslanja na pravilo koje baza
ne provodi. **Prijedlog (5.1, jeftino):** dodati
`CHECK (is_correct = true OR error_type IS NOT NULL)` na `attempts` u istoj migraciji
koja stvara `hint_requests` — pretvara invarijantu iz izmjerene u **provedenu**. Točno
poučak #55, primijenjen unaprijed umjesto unatrag.

### H3.2 Broji li se DJELOMIČAN pokušaj kao promašaj? ✅ DA — i to je najjači slučaj

Tehnički: `row_mismatch` je `is_correct = false`
([evaluation.py:206-209](backend/agents/evaluation.py#L206-L209)), pa uvjet iz H3.1
hvata i njega. Ali odgovor ne smije stati na tome.

**Pedagoški — `row_mismatch` je slučaj u kojem hint vrijedi NAJVIŠE:**

- `feedback.ts` ga zove **„Skoro! Stupci su točni, ali redovi nisu."**
  ([feedback.ts:49](frontend/src/lib/feedback.ts#L49)) — student je dokazano razumio
  projekciju, a promašio filtriranje/spajanje/grupiranje. To je **uska, imenovana**
  praznina, dakle najbolji mogući ulaz za savjet.
- Suprotno vrijedi za `syntax_error` (prazan editor) — ondje hint nema što reći.
- Uskratiti savjet studentu koji je najbliže rješenju, a dati ga onome koji je dalje,
  bilo bi **obrnuto od pedagoške namjere**. Djelomičan XP nagrađuje napredak; hint bi
  ga trebao pratiti, ne isključivati.
- BKT to potvrđuje s druge strane: `row_mismatch` ne ruši `p_L` kao potpun promašaj,
  pa je student u zoni u kojoj jedan pomak rješava zadatak — definicija ZPD-a na koju
  se recommender oslanja.

**Posljedica za pokrivenost (§G5.4):** `row_mismatch` × koncept mora biti **prvi**
prioritet u seedu, ne jedan od četiri ravnopravna.

### H3.3 Iz kojeg pokušaja se uzima `error_type`

Tri kandidata, i samo jedan je konzistentan:

| pravilo | problem |
|---|---|
| „postoji **ijedan** netočan pokušaj" | gumb ostaje aktivan i nakon što je zadatak riješen; hint bi govorio o **zastarjeloj** grešci |
| „**zadnji netočan** pokušaj" | isto — ne relocka nakon rješenja, i traži zaseban upit uz `solved` |
| ✅ **„ZADNJI pokušaj je netočan"** | — |

🔴 **Preporuka: `ORDER BY attempt_number DESC LIMIT 1` mora imati `is_correct = false`.**

```sql
SELECT a.error_type
FROM attempts a
WHERE a.user_id = :uid AND a.task_id = :tid
ORDER BY a.attempt_number DESC
LIMIT 1;
-- NULL (nema retka ILI zadnji je točan) ⟺ gumb neaktivan
```

**Zašto je to jedini konzistentan izbor:**

- **jamči `error_type IS NOT NULL`** kad je otključano (H3.1) — pa `hint_requests.error_type NOT NULL` (H3.6) stoji;
- **automatski relocka** kad student riješi zadatak — odgovor na vaše pitanje „što ako je zadnji točan a raniji netočan": **gumb se zaključa**, i to je ispravno, jer je hint pomoć za mjesto na kojem student **jest**, ne arhiva onoga gdje je bio;
- daje **jedan jednoznačan** `after_attempt_id` (H3.6);
- **jedno polje u ugovoru** nosi i uvjet i klasifikaciju (H3.4).

Rubni slučaj koji ostaje: student riješi zadatak pa ga otvori ponovno i pogriješi →
gumb se **ponovno** otključa. To je željeno ponašanje, ne propust.

### H3.4 🔴 KAKO FRONTEND ZNA da je otključano

Slažem se da in-session React stanje otpada — reload bi zaključao gumb studentu koji je
promašio, a `key` reset po tasku ([TaskPage.tsx:112](frontend/src/pages/TaskPage.tsx#L112))
čisti upravo takvo stanje pri svakoj promjeni zadatka.

**(a) `/attempts` s filtrom po `task_id` — 🔴 FILTAR NE POSTOJI.**

Citat potpisa rute ([routes.py:599-604](backend/app/api/routes.py#L599-L604)):

```python
@router.get("/attempts", response_model=Page[AttemptItem])
async def get_attempts(
    user: User = Depends(get_current_user),
    limit: int = Query(_LIMIT_DEFAULT),
    offset: int = Query(0),
) -> Page[AttemptItem]:
```

**Samo `limit` i `offset`.** `_read_attempts`
([routes.py:543](backend/app/api/routes.py#L543)) filtrira isključivo
`Attempt.user_id == user_id`; `task_id` se **vraća** u odgovoru, ali se po njemu **ne
filtrira**. `schema.d.ts` odražava isto — `paths["/attempts"]["get"]` nema
`task_id` parametar.

Dodatna zamka: `_LIMIT_DEFAULT = 20`, `_LIMIT_MAX = 100`
([routes.py:83-84](backend/app/api/routes.py#L83-L84)), a redoslijed je
`created_at DESC`. Student koji je u međuvremenu radio druge zadatke **ne bi imao** svoj
pokušaj na *ovom* zadatku u prvoj stranici. Klijentsko filtriranje po `task_id` bi bilo
**pogrešno**, ne samo skupo. Dakle (a) traži **i** izmjenu backenda **i** +1 mrežni poziv.

**(b) Novo polje u postojećem odgovoru — ✅ PREPORUKA.**

`TaskDetailResponse` je već dohvaćen pri montiranju
([useTask.ts:11-25](frontend/src/hooks/useTask.ts#L11-L25): `api.GET("/task/{task_id}")`) i već
nosi izvedeno stanje po korisniku — `solved`
([schemas.py:140-142](backend/app/api/schemas.py#L140-L142)), računat identičnim upitom
nad `attempts` ([routes.py:350-360](backend/app/api/routes.py#L350-L360)).
**Presedan je doslovan.**

Polje: **`last_attempt_error_type: str | None`** — ne `hint_unlocked: bool`.

> Ugovor opisuje **stanje baze**, ne **politiku značajke**. Ako se politika ikad
> promijeni (npr. „hint i nakon dva promašaja"), `bool` bi tražio novu izmjenu
> ugovora; `error_type` ne bi. Uz to isto polje odmah nosi klasifikaciju, koju UI može
> upotrijebiti za tekst neaktivnog stanja bez drugog poziva.

**(c) Izvedeno iz odgovora `/attempt` + dohvat pri montiranju** — to je (b) plus ručno
održavanje, jer dohvat pri montiranju **jest** (b). `AttemptResponse.feedback.error_type`
već postoji, pa se stanje nakon predaje osvježava bez ijednog poziva; nedostaje samo
stanje **pri dolasku**, što (b) daje. **(c) se svodi na (b) i ne razmatra se zasebno.**

**Usporedba:**

| | dodatnih poziva pri otvaranju zadatka | backend izmjena | `schema.d.ts` |
|---|---|---|---|
| (a) | **+1** (`GET /attempts?task_id=`) | ✅ nova query param + filtar u `_read_attempts` | +1 param na `/attempts` |
| **(b)** | **0** | polje u `_read_task_detail` + `TaskDetailResponse` | **+1 polje** |
| (c) | 0 (= (b)) | = (b) | = (b) |

🔴 **STANI-I-JAVI (H3.4) — TOČAN `schema.d.ts` DIFF.**

Ovo je jedina stavka koja proširuje popis iz §G6.3. Konačan popis:

| shema | izmjena | izvor |
|---|---|---|
| `components["schemas"]["MeResponse"]` | **+ `hints_enabled: boolean`** | §B.4.3 |
| **`components["schemas"]["TaskDetailResponse"]`** | 🔴 **+ `last_attempt_error_type?: string \| null`** | **H3.4(b) — NOVO** |
| `components["schemas"]["HintRequest"]` | **nova** — `task_id: number` | §B.4.2 |
| `components["schemas"]["HintResponse"]` | **nova** — `hint_text: string` · `source: string` · `concept?: string \| null` · `remaining?: number \| null` | §B.4.2 |
| `paths["/hint"]["post"]` | **nov** | §B.4.2 |
| ~~`AttemptRequest.hint_requested`~~ | **ne** — povučeno u G6.2 | — |
| ~~`paths["/attempts"]` param~~ | **ne** — (a) odbijena | — |

`hint_requests` ostaje interna tablica i u `schema.d.ts` ne ulazi.

### H3.5 🔴 SUKOB S §G5.4 — otključan gumb, prazan odgovor

Sukob je stvaran: gumb je aktivan jer je student promašio, ali ruta može vratiti
**503 `hint_unavailable`** (nema koncept-parnog retka **i** LLM nedostupan).

**Prvo, opseg sukoba — uži je nego što izgleda.** Uz H2 (read-only `hints`), LLM je
**primarni** izvor, a `hints` fallback. 503 zato traži **dva istodobna uvjeta**:
LLM nedostupan **I** nepokriven koncept. Dok LLM radi, 503 se ne događa.

| razrješenje | ocjena |
|---|---|
| **(a)** otključavanje ovisi i o pokrivenosti | 🔴 **ODBIJENO.** Dva neovisna razloga: (1) `enabled/disabled` **odaje koje koncepte pokrivamo** — sučelje curi stanje internog korpusa; (2) 🔴 **mijenja se tijekom evala** kako se tablica puni → dostupnost značajke postaje **nekontrolirana varijabla**, pa dva sudionika prolaze različit sustav. To je razred **#54** (valjanost mjerenja), i za rad je skuplje od svake tehničke cijene |
| **(b)** uvijek otključano nakon promašaja, 503 → poštena poruka u slotu | ✅ **kao MEHANIZAM** — obrazac već postoji (`ErrorState` s `onRetry`, §D.4), slot je ispod akcijskog reda pa ne dira mjerenje N-20, a poruka je istinita |
| **(c)** proširiti korpus tako da 503 bude nemoguć za aktivne koncepte | ✅ **kao CILJ** — **104 retka** (26 koncepata × 4 koncept-ovisna tipa, §G5.3), +3 za `timeout` na spojnim konceptima = 107 |

🔴 **STANI-I-JAVI (H3.5) — ODABRANO RAZRJEŠENJE: (b) kao mehanizam + (c) kao pokrivenost.**

Konkretno: **5.0 floor se diže s 32 na 104 retka.** Obrazloženje trampe, pošteno:

- **Cijena:** 104 kurirana teksta umjesto 32. Generiranje kroz infrastrukturu Faze 2
  stoji ~0,25 $; **stvarni trošak je ljudski pregled** — 104 kratka teksta, uz kriterij
  §G5.4 koji je već napisan.
- **Što se dobiva:** dostupnost hinta prestaje ovisiti o tome je li LLM gore, pa je
  **ista za svakog sudionika kroz cijeli eval**. Uz eval bez nadzora na javnom URL-u to
  nije udobnost nego preduvjet usporedivosti.
- **Zašto ne ostati na 32:** tada je hint dostupan za 41 % zadataka pod ispravnim LLM-om,
  a za manjinu pod ispadom — i to se u radu mora prijaviti kao ograničenje mjerenja.

**(b) ostaje potreban i uz (c)**, jer 503 i dalje može doći iz rubnih stanja
(neaktivan koncept, redak izbrisan, LLM ispao usred `INSERT`-less puta). Poruka u
slotu: *„Savjet trenutno nije dostupan. Pokušaj ponovno za koji trenutak."* — s
`onRetry`, kao svaki drugi `ErrorState`.

### H3.6 ATRIBUCIJA: izravan FK umjesto temporalnog joina — ✅ PRIHVATITI

Uz odluku korisnika hint **uvijek** sjedi između pokušaja N i N+1, pa je sidro
jednoznačno i ne mora se rekonstruirati.

```sql
after_attempt_id  integer NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
error_type        varchar(100) NOT NULL          -- bilo NULL
```

**Rubni slučajevi iz §G6.2 — što nestaje, što ostaje:**

| slučaj | prije (temporalni join) | uz FK |
|---|---|---|
| hint zatražen pa zadatak napušten | dvosmislen — nema sljedeće predaje za sidro | ✅ **nestaje** — sidro je pokušaj **prije**, koji uvijek postoji |
| dva hinta između dvije predaje | join ih ne razlučuje | ✅ **nestaje** — oba retka nose isti `after_attempt_id`, broje se trivijalno |
| hint nakon zadnje predaje | rubni slučaj prozora | ✅ **nestaje** — isti `after_attempt_id`, bez sljedećeg pokušaja |
| „je li hint **utjecao** na pokušaj N+1" | inferencija | 🔴 **ostaje** — FK daje sidro, ne uzročnost |
| „je li student hint **pročitao**" | nemjerljivo | 🔴 **ostaje** nemjerljivo (mjerenje bi tražilo telemetriju sučelja, izvan opsega) |

**Nuspojava koja ide u plus:** `ON DELETE CASCADE` na `after_attempt_id` daje **drugi
neovisan put brisanja** po osobi. `purge_demo_users.py` briše `attempts`
**eksplicitno** (jedna od „3 eksplicitno" iz #46) — a `attempts.user_id` **nema**
`ondelete` ([models.py:185](backend/app/db/models.py#L185)), pa se na `users` CASCADE ne
može osloniti. S oba FK-a (`user_id → users` i `after_attempt_id → attempts`, oba
CASCADE) `hint_requests` se čisti **kojim god redoslijedom** purge išao. Robusnije od
oslanjanja na jedan put.

**Cijena:** `error_type NOT NULL` oslanja se na invarijantu koda (H3.1). Zato prijedlog
`CHECK` ograničenja iz H3.1 nije kozmetika — bez njega jedno buduće mjesto koje piše
`attempts` mimo `persist_attempt` ruši `INSERT` u `hint_requests`, i to na produkciji,
ne u testu.

**Revidirana shema §G6:**

```sql
hint_requests(
  id                serial      PRIMARY KEY,
  user_id           integer     NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
  task_id           integer     NOT NULL REFERENCES tasks(id),
  after_attempt_id  integer     NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,  -- H3.6
  error_type        varchar(100) NOT NULL,                                            -- H3.6
  source            varchar(16)  NOT NULL,          -- 'llm' | 'fallback'
  hint_id           integer      NULL REFERENCES hints(id) ON DELETE SET NULL,        -- H1.2
  hint_text         text         NOT NULL,                                            -- H1.2
  created_at        timestamptz  NOT NULL DEFAULT now()
)
```

### H3.7 🟡 A11Y: neaktivan gumb i pristupačnost razloga

**Kako se `disabled` rješava drugdje** — jedan obrazac, iz `buttonVariants`
([button.tsx:16](frontend/src/components/ui/button.tsx#L16)):

```
disabled:pointer-events-none disabled:opacity-50
```

Potrošači: `Run` (`disabled={!canRun}`,
[TaskPage.tsx:422](frontend/src/pages/TaskPage.tsx#L422)) i `Submit`
(`disabled={!canSubmit}`, [TaskPage.tsx:431](frontend/src/pages/TaskPage.tsx#L431)) —
dakle **nativni `disabled`**, bez `aria-disabled`, bez teksta razloga.

🔴 **Zašto se taj obrazac ovdje NE može preslikati.** Kod Run/Submit razlog je
samorazumljiv (prazan editor) i **vidljiv na istom ekranu**. Kod hinta razlog je
**pravilo koje student ne može vidjeti** („moraš prvo pokušati"). Nativni `disabled`
uklanja element iz tab-reda, pa je svaki `title` tooltip **nedostižan tipkovnici i
čitaču ekrana** — informacija postaje isključivo hover-only.

**Ocjena po kriterijima:**

| SC | nativni `disabled` + `title` | prijedlog |
|---|---|---|
| **2.1.1 Keyboard (A)** | 🟡 formalno ne pada (onemogućena kontrola nije „funkcionalnost"), ali razlog je **nedostupan** tipkovnicom | ✅ gumb ostaje fokusabilan, aktivacija otkriva razlog |
| **4.1.2 Name, Role, Value (A)** | 🟡 stanje se prenosi (`disabled`), razlog **ne** | ✅ `aria-disabled="true"` + `aria-describedby` na tekst razloga |
| **1.4.13 Content on Hover (AA)** | 🔴 `title` tooltip nije ni dismissible ni hoverable | ✅ **nema tooltipa** |
| **1.4.3 Contrast (AA)** | 🔴 **nemjereno** — `opacity-50` nad `bg-card` | v. dolje |

**Predloženi oblik:**

```tsx
<Button
  variant="outline"
  aria-disabled={!hintUnlocked || undefined}
  aria-describedby={!hintUnlocked ? "hint-lock-reason" : undefined}
  onClick={hintUnlocked ? requestHint : undefined}
>
  <Lightbulb data-icon="inline-start" aria-hidden="true" />
  Zatraži hint
</Button>
```

— `aria-disabled` umjesto `disabled`: gumb ostaje u tab-redu i fokusabilan, stanje se
i dalje najavljuje. Razlog živi kao **vidljiv tekst** u hint slotu (`id="hint-lock-reason"`),
ne u tooltipu: *„Savjet je dostupan nakon prvog pokušaja — probaj predati rješenje."*
Isti slot koji nosi i hint i `rate-limited` poruku (H3.5), dakle nula nove strukture.

🔴 **Poučak N-4, primijenjen unaprijed.** N-4 je zapis o tome kako je a11y tvrdnja bila
**dvostruko kriva** — krivi SC (2.4.11 umjesto 1.4.11) i **premala mjerna baza** (jedan
par boja prikazan kao cijela slika). Zato ovdje **ne tvrdim** da neaktivno stanje prolazi
kontrast. `disabled:opacity-50` / `aria-disabled:opacity-50` kompozitira tekst gumba nad
`bg-card`, i po N-4 metodi (oklch → sRGB, alpha kompozitirana nad **navedenom** plohom)
to treba **izmjeriti prije nego se tvrdi**. Ako padne ispod 4,5:1, rješenje nije
opacity nego zaseban token — ali to je **mjerenje, ne pretpostavka**, i ide u exit 5.2.

### H3.8 Vrijedi li mjerenje N-20 i dalje? ✅ DA

Odluka korisnika je da gumb **postoji od početka, samo je neaktivan**. Posljedice za
mjerenje:

| | |
|---|---|
| broj elemenata u akcijskom redu | **konstantan** — 2 (hint + Run/Submit grupa) kroz cijeli rad |
| natpis | **konstantan** — „Zatraži hint" u oba stanja (G7: zamrznut) |
| `aria-disabled` vs `disabled` | mijenja **stiliziranje** (`opacity`), **ne layout** — `opacity` ne utječe na `getBoundingClientRect` |
| ikona, `gap`, `px` | nedirnuti |

**Izmjerene brojke iz §B.6.2 / §G7.3 vrijede nepromijenjeno**: hint gumb 119 px, slack
2,47 px na 768 px, visina kartice 540/640 px konstantna. Test iz §G7.1 (`row` height
`toBe(44)`) hvata i neaktivno i aktivno stanje jer mjeri isti DOM.

🔴 **Jedan uvjet koji test mora čuvati:** natpis se **ne smije** razlikovati po stanju.
Svaka varijanta tipa „Zatraži hint (zaključano)" ili „Zatraži hint (1/3)" izmjereno
wrapa (§G7.2) i ruši mjerenje. Zato razlog i brojač idu u **slot**, ne u natpis —
što je već odlučeno u H3.5 i H3.7 iz drugih razloga. Tri neovisna razloga za istu
odluku.

**Jedini slučaj koji NIJE pokriven ovim mjerenjem:** `hints_enabled = false` (§B.5.5),
gdje se gumb uklanja iz DOM-a. To je izmjereno zasebno u §B.6.2 (stupac „BEZ hinta") i
visina kartice ostaje ista. Pokriveno.

---

## C — PRIJEDLOG STAGEA FAZE 5

> ⟳ **REVIDIRANO 2026-08-11 prema G1 / G5 / G6, pa prema H1 / H2 / H3.** Izmijenjeni
> entry/exit označeni su ⟳; ono što je ukinuto prekriženo je.

Redoslijed je izveden iz nalaza, ne iz plana. **5.0 je preduvjet svemu ostalom**,
jer bez fallbacka HintAgent nema donju granicu ponašanja.

### 5.0 — Preduvjeti: fallback + suglasnost 🔴 BLOKATOR

| | |
|---|---|
| **Entry** | Ovaj dokument odobren; odluka B.1.4 (varijanta A ili B) donesena; odluka B.2.3 (provider) donesena; ⟳ odluka G6 (tablica `hint_requests` da/ne — jer mijenja opseg 5.2) |
| **Sadržaj** | Errata #59 upisana. ⟳⟳ `hints` seedana sa **104 koncept-parna retka** (svih 26 koncepata × 4 koncept-ovisna `error_type`, §H3.5) — ~~32~~ podignuto, ~~7 generičkih~~ ukinuto. **Prioritet: `row_mismatch` × koncept prvi** (§H3.2). ~~240 predgeneriranih hintova za prvi pokušaj~~ 🔴 **POVUČENO** (§G1.3/G1.4 povučeni odlukom korisnika). `participation.ts` dopunjen odabranom varijantom. `CLAUDE.md:17` i `faza-3-plan.md:240` usklađeni s odlukom o provideru. |
| **Exit** | ⟳⟳ `SELECT count(*) FROM hints WHERE concept_id IS NOT NULL` **≥ 104**, i pokriveni su **svi** koncepti iz §G5.3 × 4 tipa (upit koji nabraja rupe mora vratiti 0 redaka) · **`… WHERE concept_id IS NULL` = 0** · seed idempotentan · ⟳ **test kriterija G5.4**: nijedan `hint_text` nije parafraza `ERROR_TEXT[error_type]` i svaki sadrži pojam specifičan za koncept · ⟳ **test guarda G2.3** nad seedanim korpusom: nijedan ne sadrži `expected_query` ni vrijednost iz `expected_result` · `participation.ts` tekst pregledan i odobren |
| **Ne dira** | nula izmjena u `agents/`, `app/api/`, `frontend/src/pages/` |

### 5.1 — HintAgent iza flaga, bez UI-ja

| | |
|---|---|
| **Entry** | 5.0 exit |
| **Sadržaj** | `agents/hint_agent.py` · `Ontology.REQUEST_HINT` · `jids.py` + Prosody + `.env` · `config.py`: `ANTHROPIC_API_KEY`, `USE_LLM_HINTS`, `HINT_LLM_TIMEOUT=8`, `HINT_TIMEOUT=12`, `HINT_RATE_LIMIT=10` · `gateway_agent.py` template `t_hint` · `POST /hint` · ⟳⟳ **uvjet otključavanja: zadnji pokušaj je netočan** (§H3.3) — ~~grananje po `error_type IS NULL`~~ povučeno · ⟳⟳ migracija: `hint_requests` u konačnoj shemi §H3.6 **+ `CHECK (is_correct = true OR error_type IS NOT NULL)` na `attempts`** (§H3.1) · ⟳ rate limit iz **`hint_requests`** · ⟳ **redigiran `log_message` `content`** (§G3.4c) · `AnthropicClient` s `max_retries=0` |
| **Exit** | `POST /hint` vraća hint na živom lancu · **s `USE_LLM_HINTS=false` vraća 503 `hints_disabled`, bez ijednog odlaznog HTTP poziva (dokazano mrežnim tragom, ne pretpostavkom)** · ⟳⟳ **`hints` je READ-ONLY u runtimeu — dokazano ishodom:** `SELECT count(*) FROM hints` identičan prije i poslije serije od 10 hintova (od kojih ≥3 kroz LLM) (§H2.4) · ⟳⟳ **`POST /hint` na zadatku bez netočnog pokušaja vraća 409/403, ne hint** · fallback dokazan gašenjem ključa · 429 dokazan 11. zahtjevom · 🔴 **`POST /attempt` p95 nepromijenjen pod 3 paralelna hint zahtjeva** (§B.4.4) · ⟳ **test G2.3** nad `build_hint_payload` za svih 80 aktivnih zadataka · ⟳ **`agent_messages_log` nakon 10 hintova ne sadrži ni `hint_text` ni `submitted_query`** (SQL provjera, ne čitanje koda) · ⟳⟳ **`hint_requests` nakon 10 hintova ima 10 redaka, svaki s `after_attempt_id` koji pokazuje na netočan pokušaj** · `coordinator.py` byte-identičan |
| **Ne dira** | `frontend/`, `schema.d.ts` još ne (ruta postoji, klijent je ne zove) · ⟳ **`persistence.py` i `evaluate-query` payload — NE diraju se uopće** (G6.2) |

### 5.2 — UI ⟳ (bez izmjene `AttemptRequest`)

| | |
|---|---|
| **Entry** | 5.1 exit |
| **Sadržaj** | ⟳⟳ **`MeResponse.hints_enabled` + `TaskDetailResponse.last_attempt_error_type`** — dvije izmjene postojećih shema, nula dodatnih mrežnih poziva (§H3.4) · `npm run gen:api` · hint gumb, ⟳ **natpis zamrznut na „Zatraži hint" u OBA stanja** (G7 + H3.8) · ⟳⟳ **neaktivno stanje kroz `aria-disabled` + `aria-describedby`, razlog kao vidljiv tekst u slotu, bez tooltipa** (§H3.7) · zaseban slot iznad `FeedbackPanel`a · 6 stanja iz §D.4 + `locked`, ⟳ **ni brojač ni razlog NISU u natpisu** (G7.2, H3.5, H3.7 — tri neovisna razloga) · `data-testid` na editor box i akcijski red |
| **Exit** | ⟳⟳ `schema.d.ts` diff je **točno** popis iz §H3.4, ništa više · 🔴 **re-verifikacija sva 4 stanja panela s ocjenom na živom agentskom lancu** (netočno / djelomično / točno / već riješeno) — dodir eval-verificiranog puta · ⟳ **N-20 test iz §G7.1 u smoke suiteu i prolazi** · ⟳⟳ **gumb se otključa nakon netočne predaje i OSTAJE otključan preko reloada** (e2e: predaj krivo → reload → gumb aktivan) · ⟳⟳ **relocka se nakon točne predaje** (§H3.3) · ⟳⟳ 🔴 **kontrast neaktivnog natpisa IZMJEREN po N-4 metodi** (oklch → sRGB, alpha kompozitirana nad `bg-card`) — ne tvrdi se, mjeri se · visina kartice izmjerena na 768/1280/1920 u sva tri stanja (aktivan / neaktivan / odsutan), nepromijenjena · `tsc -b` · `vite build` · `oxlint` · `prettier` · `npm run e2e` |

### 5.3 — Suglasnost kao zapis (ako se ide dalje od teksta)

| | |
|---|---|
| **Entry** | 5.2 exit; **odluka korisnika** — ovaj stage je opcionalan |
| **Sadržaj** | Ono što je `participation.ts:19-21` odgodio za Fazu 5: bilježena suglasnost traži novu kolonu → migracija (🔴 izmjena sheme = pitanje prije izvedbe) |
| **Exit** | migracija up/down obje testirane · postojeći računi migrirani s eksplicitnom vrijednošću, ne NULL |

### Što se NE gradi u Fazi 5

- **WebSocket** — rezan u 4.6, ostaje rezan
- **Personalizacija hinta po `p_L`** ako se prihvati cache-kroz-`hints` (§B.5.3) — traži kolonu, dakle 5.3 ili Fazu 6
- ~~⟳ **Puna pokrivenost `(error_type, concept_id)`** — u 5.0 ide 32, ostatak puni upotreba~~ ⟳⟳ **PREMJEŠTENO U 5.0**: 104 retka je sada floor (§H3.5), jer djelomična pokrivenost čini dostupnost hinta nekontroliranom varijablom
- ⟳⟳ 🔴 **Runtime UPIS u `hints` — u cijelosti.** Tablica je **read-only u runtimeu** i mijenja se isključivo seed skriptom. Cache-kroz-`hints` iz §B.5.3 se **povlači**: izmjereno vrijedi **0,01–0,06 $** na cijeli eval (§H2.3), a otvara kanal kojim nekuriran LLM tekst — moguće s rekonstruiranim rješenjem (§G2.3) — trajno ulazi u korpus i servira se svim sljedećim studentima. `hints` je **kurirani fallback**, ne cache
- ⟳ **`hint_requested = True` u `attempts`** — kolona ostaje hardkodirana na `False`; atribucija ide preko `hint_requests.after_attempt_id` (§H3.6). **Ide u eval runbook** da nitko ne pročita `false` kao „hintovi nisu korišteni"
- ⟳⟳ **Predgeneriranje hintova za prvi pokušaj** — 240 tekstova iz §G1.3; povučeno odlukom korisnika (nema slučaja B)
- ⟳⟳ **Telemetrija „je li student pročitao hint"** — jedini rubni slučaj iz §G6.2 koji ni FK ne rješava (§H3.6); tražila bi mjerenje sučelja, izvan opsega

---

## 🔴 STANI-I-JAVI — sažetak dopune H

| # | stavka | traži |
|---|---|---|
| **H1.2** | 🔴 **PRESUDA: sam tekst hinta NIJE osobni podatak; veza `user_id → hint_text` JEST.** Tekst je izlaz sustava iz omeđenog skupa, dijeljen među studentima — ne studentov unos. Veza je izvedeni podatak o osobi, ali **isti zaključak već nosi `attempts.error_type` + `task_id`** od Faze 1. **Pohrana ne pogoršava #46 nego ga ublažava** — premješta odgovor na „koji hint je student vidio" iz neizbrisivog `agent_messages_log`a u tablicu s CASCADE-om. | **odobrenje `hint_id NULL` + `hint_text NOT NULL`.** Obje kolone: FK daje analitičku grupu, `hint_text` je **snimka** (FK bi vraćao tekuću vrijednost i tiho prepisao povijest — isti razlog zbog kojeg `xp_log` nosi `delta`) |
| **H2.2** | 🔴 **PREPORUKA: (a) `hints` READ-ONLY u runtimeu.** Odlučuje asimetrija posljedice, ne cijena: cijeli cache vrijedi **0,01–0,06 $** na eval (hit-rate 4–20 % × ~120 hintova), a (b) riskira da tekst s rekonstruiranim rješenjem trajno uđe u korpus i posluži se svim sljedećim studentima. (a) je **dokaziva ishodom** (broj redaka nepromijenjen nakon 10 hintova); (b) nije — „korpus ostaje čist kroz eval" je runtime svojstvo koje se zna tek nakon evala. | **potvrdu (a)** i izmjene exita 5.1 + retka „Što se NE gradi" iz §H2.4 |
| **H3.1** | ✅ **NEMA STANI-I-JAVI — uvjet JAMČI klasifikaciju.** Tri neovisna dokaza: svih 7 `is_correct=False` izlaza u `evaluation.py` postavlja ne-`None` `error_type`; živa baza daje **0 protuprimjera** (13 f/not-null, 21 t/null); `persist_attempt` je **jedini** proizvodni pisac. 🟡 Ali je to invarijanta **koda, ne sheme** — `error_type` je nullable bez `CHECK`a. | **odobrenje `CHECK (is_correct = true OR error_type IS NOT NULL)`** u istoj migraciji — pretvara izmjerenu invarijantu u provedenu, jer se `hint_requests.error_type NOT NULL` na nju oslanja |
| **H3.4** | 🔴 **`/attempts` NEMA `task_id` filtar** — citat potpisa: samo `limit`/`offset`; uz `_LIMIT_DEFAULT=20` i `created_at DESC` klijentsko filtriranje bi bilo **pogrešno**, ne samo skupo. **Preporuka (b):** `TaskDetailResponse.last_attempt_error_type` — `/task/{id}` se već dohvaća pri montiranju (`useTask.ts:20`), presedan je `solved`. **Nula dodatnih poziva.** Polje opisuje stanje baze, ne politiku značajke. | **odobrenje `schema.d.ts` diffa iz §H3.4** — 5 stavki, od kojih je `TaskDetailResponse` jedina koja proširuje popis §G6.3 |
| **H3.5** | 🔴 **ODABRANO: (b) mehanizam + (c) pokrivenost.** (a) **odbijena** iz dva razloga: sučelje bi odavalo koje koncepte pokrivamo, i dostupnost bi se **mijenjala tijekom evala** → nekontrolirana varijabla (razred #54). **5.0 floor se diže s 32 na 104 retka**, čime 503 postaje nemoguć dok LLM radi ili ne radi. (b) ostaje za rubna stanja, s `ErrorState` obrascem koji već postoji. | 🔴 **potvrdu podizanja floora 32 → 104.** Trošak nije novac (~0,25 $ generiranja) nego **ljudski pregled 104 kratka teksta** |
| **H3.6** | ✅ **FK prolazi.** `after_attempt_id NOT NULL REFERENCES attempts(id) ON DELETE CASCADE` + `error_type NOT NULL` uklanja **sva tri** rubna slučaja temporalnog joina; ostaju samo uzročnost i „je li pročitao". Nuspojava u plus: **drugi neovisan put CASCADE brisanja** — bitno jer `attempts.user_id` **nema** `ondelete`, pa se purge na `users` CASCADE ne može osloniti | — (uključeno u odobrenje migracije iz H1.2) |
| **H3.7** | 🟡 **Nativni `disabled` obrazac iz `buttonVariants` se ovdje ne može preslikati.** Kod Run/Submit razlog je vidljiv na ekranu; kod hinta je pravilo koje student ne vidi, a `disabled` ga izbacuje iz tab-reda pa je `title` nedostupan tipkovnici i čitaču. Prijedlog: `aria-disabled` + `aria-describedby` + razlog kao **vidljiv tekst u slotu**, bez tooltipa. Po poučku **N-4** kontrast neaktivnog natpisa se **ne tvrdi nego mjeri** — u exit 5.2 | **odobrenje `aria-disabled` obrasca** (odstupanje od zatečenog `disabled` uzorka) |
| **H3.8** | ✅ **N-20 mjerenje vrijedi nepromijenjeno.** Gumb je renderiran od početka, broj elemenata u redu konstantan, natpis isti u oba stanja, `opacity` ne utječe na `getBoundingClientRect`. **Uvjet:** natpis se ne smije razlikovati po stanju — što H3.5 i H3.7 ionako nalažu iz drugih razloga | — |

---

## 🔴 STANI-I-JAVI — sažetak dopune G

| # | stavka | traži |
|---|---|---|
| **G1.3** | **Hint za PRVI pokušaj je ispod praga informativnosti.** 240 kombinacija po zadatku (80 × 3 `p_L` razreda), 78 po konceptu — oboje ispod ~300. Ulaz je u cijelosti statički. **Runtime LLM poziv za taj slučaj ne nosi informaciju**; predgeneriranje svih 240 stoji 0,58 $ (Haiku), jednom, s ljudskom provjerom. | **odobrenje grananja iz G1.4**: prvi pokušaj → predgenerirano, ponovljeni → runtime. Time se i opseg §B.1 sužava na ponovljene pokušaje |
| **G2.1** | **NE — rješenje ne napušta sustav pod mojom preporukom.** Ali guard je na 3 mjesta, nijedno ne pokriva izravan put gateway → HintAgent, i **nijedan test ga ne čuva** (13 pogodaka u testovima koriste `expected_query` kao ulaz, nijedan ne tvrdi da ga nema u izlazu). Jedini dokaz je jednokratan sken iz 4.5. Razred #55/N-18. | **odobrenje testa iz G2.3** kao exit kriterija 5.1 — provjera **sadržaja**, ne imena ključa, i nad LLM izlazom, ne samo ulazom |
| **G3.3** | **+540 do +1 800 zapisa u `agent_messages_log`, tj. +7,3 % do +24,3 %** nad izmjerenih ~7 400 iz #46 (3 retka po hintu, izmjereno na 397 stvarnih `/next-task` razgovora). U `content`u bi bio i upit (varijanta A) i **tekst hinta**. | **odluku o G3.4(c)**: redigiran `content` čuva cijeli FIPA trag za rad i admin viewer, a hint promet prestaje biti osobni podatak — brojka ostaje, izloženost nestaje |
| **G5.2** | **DA — 4 od 7 mojih generičkih fallback tekstova su čista parafraza** `ERROR_TEXT` iz `lib/feedback.ts`, koji student čita 200 px niže dok kliká gumb. Preostala 3 dodaju po jednu riječ. Prijedlog iz §B.3.4 **pada**. Razred #57 (instrument kalibriran prema zatečenom stanju). | **odobrenje revidiranog minimuma iz G5.4**: 32 koncept-parna retka, generički sloj **ukinut**, a kad nema koncept-parnog retka ruta vraća 503 → gumb `unavailable` umjesto parafraze |
| **G6** | **`hint_requests` tablica uklanja izmjenu FIPA protokola.** Trampa: jedna Alembic migracija **umjesto** dodira `AttemptRequest` + `persist_attempt` + `evaluate-query` payloada — dakle umjesto dodira eval-verificiranog puta. CASCADE rješava per-user brisanje koje `agent_messages_log` ne može. | 🔴 **izmjena sheme = pitanje po CLAUDE.md.** Odluka mijenja opseg 5.1 i 5.2 (17. tablica, `test_db_schema.py:23`) |
| **G7** | **Prihvaćeno: responzivno skrivanje riječi se povlači.** `gap-3` → `gap-2` donosi točno +4 px protiv manjka od 15–27 px — nije popravak. Natpis se zamrzava na „Zatraži hint", popravak je test iz G7.1. Brojač limita izmjereno wrapa pod svakom `gap` varijantom do ~790 px → ide u tooltip / slot ispod gumba, ne u label. | **odobrenje N-20 testa** kao exit kriterija 5.2 (traži dva `data-testid`) |

---

## 🔴 STANI-I-JAVI — sažetak (dio B)

| # | stavka | traži |
|---|---|---|
| **1** | **B.1 — tekst suglasnosti.** Dvije varijante u §B.1.3, ovisne o odluci B.1.4. Tekst ide u rad. | **odluku: varijanta A (šalje upit) ili B (ne šalje)** — i, ako B, odvojenu odluku o `attempts.detail` |
| **2** | **B.3 — fallback NE POSTOJI.** `hints` tablica je prazna (0 redaka), seed je ne dira, nijedan kod je ne čita. Plan je tvrdio suprotno. | **potvrdu da 5.0 ide prvi** i da je prijedlog od 7 generičkih redaka prihvatljiv |
| **3** | **B.2 — odstupanje od plana §2.5.** Preporuka: Anthropic umjesto OpenAI-ja, `claude-haiku-4-5`. | **odluku o provideru** — pa se `CLAUDE.md:17` i `faza-3-plan.md:240` usklađuju |
| **4** | **B.4 — FIPA payload i shema ugovora.** `evaluate-query` dobiva 4. polje; `AttemptRequest` i `MeResponse` se mijenjaju. Po CLAUDE.md, izmjene FIPA protokola traže pitanje. | **odobrenje ugovora iz §B.4.2/B.4.3** |
| **5** | **B.4.4 — FSM.** HintAgent **NE blokira** `RECEIVE→EVALUATE→UPDATE→RECOMMEND→RESPOND` **pod uvjetom** da ide izravno kroz bridge (presedan `/next-task`), a ne kroz Coordinator. Kroz Coordinator bi bio blokator jer je FSM globalno serijaliziran. | **potvrdu da se ide izravnim putem** |
| **6** | **B.6 / N-20 — natpis ima 2,47 px proračuna na 768 px.** „Zatraži hint" prolazi; svaki duži natpis wrapa i produžuje karticu za 56 px. | **odabir razrješenja** (zaključati natpis / responzivan natpis / ikona-only) |

**Nije blokator, ali ide u zapisnik:** ako se prihvati brojanje limita iz
`agent_messages_log` (§B.5.2), eval volumen dobiva ~600 dodatnih zapisa koje se ne
može obrisati po osobi — proširuje opseg **#46**, ne mijenja mu narav.

---

## Što ovaj korak NIJE provjerio (iskren opseg)

- **Kvalitetu hintova** — nula LLM poziva izvedeno. Sve o pedagoškoj vrijednosti je
  pretpostavka dok se ne izmjeri na stvarnim izlazima.
- **Latenciju LLM-a u praksi** — `HINT_LLM_TIMEOUT = 8 s` je izveden iz postojećeg
  proračuna timeouta, ne iz mjerenja odziva Haikua na ovom promptu.
- **Ponašanje pod konkurencijom** — tvrdnja da hint ne blokira FSM slijedi iz čitanja
  koda (`_coordinator_template` ne propušta `request-hint`), **nije izvedena mjerenjem**.
  Zato je u exitu 5.1 kao mjerni kriterij (p95 pod paralelnim hintovima).
- **Veličinu sustavskog prompta** — ~1 500 tokena je procjena, ne `count_tokens`.
  Utječe na tvrdnju o cachingu (§B.5.4) i mora se izmjeriti prije nego se caching
  proglasi (ne)djelatnim.
- **Prosody registraciju** — postupak je u CLAUDE.md checklisti, nije izveden ni testiran.
- **N-20 na stvarnoj aplikaciji** — mjereno na harnessu s pravim buildanim CSS-om i
  doslovno kopiranim klasama, uz kontrolu koja se poklopila s aritmetikom grida na
  0,01 px. Nije mjereno na živom Task ekranu s pravim podacima; mjerenje treba
  ponoviti u 5.2 kad gumb stvarno postoji. **Isto vrijedi za `gap` mjerenja iz G7.3.**

**Dodano uz G:**

- **Raspodjela `error_type` na stvarnim studentima** — u živoj bazi je 13 attempta i
  samo dvije vrijednosti (`empty_result`, `execution_error`). Kardinalnosti iz G1.3 su
  **gornje granice iz taksonomije i sheme**, ne izmjerena raspodjela. Ako se u evalu
  pokaže da 90 % grešaka pada u dva tipa, i pokrivenost iz G5.4 i hit-rate iz G4.3
  računaju se iznova.
- **Je li 3 retka po hintu točno** — izmjereno na `/next-task` putu, koji je
  arhitektonski identičan, ali HintAgent još ne postoji. Broj se mora **ponovno
  izmjeriti** nakon 5.1, ne prepisati odavde (poučak #55).
- **Redigirani `content` (G3.4c)** — dokazuje se SQL provjerom nad logom nakon 10
  hintova, što je u exitu 5.1. Dotad je tvrdnja o „prestaje biti osobni podatak"
  **dizajnerska namjera, ne izmjereno stanje**.
- **Predgenerirani hintovi za prvi pokušaj** — 240 je izračunata gornja granica; nije
  provjereno je li za svaki od 80 zadataka uopće moguće napisati koristan hint bez
  ijednog podatka o studentovom radu. To se saznaje tek pisanjem prvih desetak.
- **Temporalni join za atribuciju hint→ishod (G6.2)** — ⟳ **bespredmetno nakon H3.6**
  (zamijenjen izravnim FK-om).

**Dodano uz H:**

- **Invarijanta `is_correct=false ⟹ error_type NOT NULL`** — dokazana čitanjem svih 9
  izlaza `evaluate()`, mjerenjem nad **34 reda** žive baze i jedinstvenošću pisca. To je
  mala baza; invarijanta drži u kodu, ali `CHECK` iz H3.1 je jedini oblik koji je čini
  **provedenom**, i on još ne postoji.
- **Hit-rate 4–20 % iz §G4.3** — izveden iz kardinalnosti, ne izmjeren. Cijela računica
  vrijednosti cachea (0,01–0,06 $) na njemu počiva. Ako se raspodjela `error_type`
  pokaže vrlo koncentriranom, hit-rate raste — ali ne dovoljno da promijeni presudu
  H2.2, jer ta počiva na asimetriji posljedice, ne na iznosu.
- **Da je 104 retka dovoljno za pokrivenost** — 26 × 4 je **shema pokrivenosti**, ne
  dokaz da za svaki par postoji smislen tekst. Neki parovi (npr. `execution_error` ×
  `select_basic`) možda nemaju što reći preko `ERROR_TEXT`a. To se saznaje tek pisanjem;
  ako se pokaže da ih je više, kriterij §G5.4 traži da se **izostave**, ne da se popune
  parafrazom.
- **`aria-disabled` obrazac (H3.7)** — nije prototipiran ni provjeren čitačem ekrana.
  Tvrdnja da prolazi 2.1.1/4.1.2 je **izvedena iz kriterija**, ne iz testa s NVDA/VoiceOver.
- **Kontrast neaktivnog natpisa** — **nemjeren**. Po N-4 to je točno mjesto na kojem se
  a11y tvrdnja ne smije iznositi bez brojke; zato je u exitu 5.2, a ne ovdje.
- **Da `hint_text` u izvozu prolazi pseudonimizaciju** — `export_eval_data.py` prevodi
  `user_id` u pseudonim, ali tekst hinta nikad nije prošao kroz taj put. Ako ijedan
  seedani tekst ikad sadrži nešto specifično za osobu (ne bi smio), pseudonimizacija ga
  ne hvata.

---

# §C — ZAPISI ZA 5.1 (odluke donesene u 5.0, ne implementirane)

Ova sekcija je *ulaz* u 5.1. Svaka stavka je odluka, ne prijedlog.

## C.1 Limit
5 hintova max, **+1 svaka 4 h**, izveden iz `hint_requests` **pri čitanju** (bez crona).
Broje se samo `source IN ('llm','fallback')` — **`unavailable` NE troši kredit**, jer
student nije dobio ništa. Upit nosi `idx_hint_requests_user_created`.

## C.2 Idempotencija
Ponovljeni zahtjev za isti `after_attempt_id` vraća **pohranjeni `hint_text`**: bez LLM
poziva, bez novog retka, bez trošenja kredita.

## C.3 Ruta ne vjeruje klijentu
Provjera „zadnji pokušaj na ovom zadatku je netočan" mora biti **i u ruti** (409/503), ne
samo u UI-ju. `aria-disabled` gumb ostaje klikabilan — mjereno u A3, prozor između predaje
i osvježenog `TaskDetailResponse`a je stvaran.

## C.4 `HintResponse` nosi `remaining` i `next_refill_at`
Inače je prazan bucket neobjašnjen. 🔴 Brojač **NIKAD u natpisu gumba** (§G7.2).

🔴 **Ako brojač na frontendu čita vlastiti query key**, taj key MORA ući u
`onSuccess` listu `useSubmitAttempt` (`invalidateQueries`, default `refetchType: 'active'`)
— inače se `remaining` ne osvježava nakon potrošenog hinta i student vidi zastarjelu
brojku. Isti mehanizam koji je u A3 izmjeren za `["task", taskId]`.

## C.5 Nalaz za rad — broj hintova nije mjera potražnje
Broj traženih hintova je **odozgo ograničen dizajnom** (5 / 4 h), pa **nije** mjera
potražnje. Ova rečenica mora stajati **svugdje gdje se brojka spominje** u radu.

## C.6 `sqlstate` na bijeloj listi (A1-dop-1)
`psycopg.Error.sqlstate` je dohvatljiv na mjestu hvatanja
([sandbox_runner.py:141-146](backend/scripts/lib/sandbox_runner.py#L141-L146)) i **gubi se
pri `str(e)`** — izmjereno: `'42703' in str(e)` je `False`. Kolona
`attempts.sqlstate VARCHAR(5) NULL` je dodana u 5.0 i **stoji prazna**; puni je 5.1 kroz
`ExecutionResult → EvaluationOutcome → persist_attempt`.

Izmjereno na živom sandboxu — kôd je zatvoren šifrarnik bez ijednog studentovog znaka,
dok poruka pored njega nosi doslovni redak upita:

| SQLSTATE | klasa | pogađa koncept |
|---|---|---|
| `42803` | `GroupingError` | `group_by`, `having_filter` |
| `42702` | `AmbiguousColumn` | `multi_table_join`, `inner_join` |
| `42703` | `UndefinedColumn` | — |
| `42P01` | `UndefinedTable` | — |
| `42601` | `SyntaxError` | — |
| `42883` | `UndefinedFunction` | — |

🔴 **Zamka imena:** SQLSTATE `42601` zove se `syntax_error`, a naš `error_type='syntax_error'`
znači **prazan editor**. Dva različita pojma pod istim imenom — ista zamka na koju
[feedback.ts:11-13](frontend/src/lib/feedback.ts#L11-L13) već upozorava. U 5.1 se ne smiju
pomiješati.

### 🔴 C.6a — kolona postoji, NITKO je ne piše: obrazac `hint_requested`

Izmjereno, `grep` po cijelom backendu bez `.venv`: **`sqlstate` nema nijednog pisca.**
Pojavljuje se samo u modelu, migraciji i shemskom testu. U bazi: **0 od 35 pokušaja ima
vrijednost.**

To je točno obrazac koji `attempts.hint_requested` nosi od Faze 1: kolona postoji u shemi
od inicijalne migracije, `persist_attempt` je **tvrdo kodira na `False`**
([persistence.py:78](backend/agents/persistence.py#L78)), nitko je nikad ne postavi na
`true`, a `/attempts` je i dalje serviraju
([routes.py:590](backend/app/api/routes.py#L590)) i `export_eval_data.py` je izvozi
([:87](backend/scripts/export_eval_data.py#L87)). U bazi: **0 od 35 `true`.** Stupac koji
u izvozu izgleda kao podatak, a mjeri isključivo činjenicu da ga nitko ne piše.

**Razlika koja `sqlstate` čini prihvatljivim, a `hint_requested` ne:** `sqlstate` ima
**imenovanog pisca i rok** — 5.1, lanac `sandbox_runner → EvaluationOutcome →
persist_attempt`. Dok se to ne dogodi, kolona je **prazna obveza, ne podatak.**

🔴 **Uvjet:** ako 5.1 ne popuni `sqlstate`, kolona se **briše**, ne ostavlja. Prazan
stupac u shemi je skuplji od nepostojećeg jer se pojavljuje u izvozu i u `\d attempts`, pa
sljedeći čitatelj pretpostavi da nešto znači. `hint_requested` je dokaz da se ta
pretpostavka doista dogodi.

**Presuda za bijelu listu selektivnog B+:** `sqlstate` **IDE** — zatvoren šifrarnik, bez
ijednog studentovog znaka, jedini signal za `execution_error`. Uvjetovano gornjim
rokom.

## C.7 Guard §G2.3 — izuzeće za `wrong_columns` (A1-dop-2)
Pod rekonstrukcijom LLM dobiva `task.expected_result[0].keys()`. Guard mora propustiti
**ključeve**, nikad **vrijednosti**. Dvodijelno, strukturni dio je primarni:

- **Dio A (strukturni, primarni).** Payload se gradi iz zatvorenog skupa polja. Polje
  `expected_columns` smije poprimiti **isključivo** `sorted(task.expected_result[0].keys())`
  i smije postojati **samo** za `error_type == 'wrong_columns'`. Nijedno drugo polje ne
  smije biti izvedeno iz `expected_result`. Test uspoređuje skup polja s bijelom listom.
- **Dio B (substring backstop).** Nad serijaliziranim payloadom: nijedan string oblik
  vrijednosti iz `expected_result[n]`, za svaki `n` i svaki ključ; ni `expected_query`,
  doslovno ni s normaliziranim razmacima.
- **Sudar:** token koji je i ključ i vrijednost → **tretira se kao vrijednost i pada**
  (fail-closed).
- **Lažni pozitivi:** čisto brojčane vrijednosti uspoređuju se kao **cijeli tokeni**, ne
  kao podniz — inače dopušteni `row_mismatch` detalj („actual=30 vs expected=3") obara
  guard na vrijednosti `3`.

Implementirano u smjeru `hints` kataloga u
[test_hints_seed.py](backend/tests/test_hints_seed.py); u 5.1 se isto pravilo primjenjuje
na LLM payload. **Exit kriterij 5.1.**

## C.8 `hints` nema UNIQUE nad `(error_type, concept_id)`
Jedinstvenost trenutno drži seeder ([seed_hints.py](backend/scripts/seed_hints.py)) i
provjerava test. Kandidat za migraciju u 5.1 — nije dodano u 5.0 jer plan traži **jednu**
reviziju.

---

# §D — DRIFT I RIZICI ZABILJEŽENI U 5.0

## D.1 Prozor od 37 ms iz A3 je svojstvo LOKALNOG mjerenja
🔴 Izmjereno **lokalno** (Vite dev server + backend na `localhost`, bez HTTPS-a):
`POST /attempt` → 200 na +10339 ms, refetch `GET /task/15` → 200 na +10376 ms. Razlika
**37 ms**.

To **nije** svojstvo sustava. Na VPS-u s HTTPS-om, TLS handshakeom i agentskim lancem
prozor je **bitno veći**. Nijedna tvrdnja u radu ne smije se osloniti na tu brojku kao na
mjeru ponašanja u produkciji; navodi se isključivo uz kvalifikaciju „mjereno lokalno".
Posljedica je zato **C.3** (provjera u ruti), ne „prozor je zanemariv".

## D.2 RIZIK: nema odvojene test baze
`pg_database` sadrži samo `tutor_main`. `pytest` piše u **istu** bazu koju koristi
aplikacija, pa je svaka nova shemska invarijanta (npr.
`ck_attempts_error_type_when_incorrect`) odmah i produkcijska — nema međukoraka na kojem
bi se namočila. Isti korijen kao ERRATA #40/#46. **Rizik, ne napomena.**

## D.3 Drift redaka
- `evaluation.py:196-198` → **`199-202`** (ispravljeno u ovom dokumentu).
- `useTask.ts:20` → **`11-25`** (ispravljeno u ovom dokumentu).
- Hook se zove **`useSubmitAttempt`**, ne `useAttempt` (ispravljeno u ovom dokumentu).
- [feedback.ts:26](frontend/src/lib/feedback.ts#L26) citira `evaluation.py:186` kao jedini
  izvor `partial` verdikta; danas je to `:209`. **Nije ispravljeno** — 5.0 ne dira
  `frontend/src/`. Za 5.2.

## D.4 preporučivač nema determinističan tie-break → **POPRAVLJENO drugdje**

> **Status:** popravljeno na grani `fix-recommender-determinizam` (s `main`a), **ERRATA
> #60**. Ne ulazi u ovu granu ni u tag `faza-5-0-preduvjeti` — blokira **deployment**
> neovisno o Fazi 5, pa ide zasebnim PR-om PRIJE ovoga. Ostatak odjeljka je zapis kako je
> nađen; mjerenja i presuda su u erratu.
>
> Jedna tvrdnja odozdo je bila **pogrešna** i ispravlja se: pisalo je da dva testa padaju.
> Ne padaju stabilno — **flaky su.** Nakon pune suite prolaze, jer `test_seed` ostavi heap
> u poretku koji daje `inner_join`; padaju kad ih zatekne drugi poredak. Kvar je time gori
> nego što je ovdje opisan: ne „dva testa padaju", nego **preporuka se mijenja između
> pokretanja**.

Nađeno pri izvođenju exit kriterija „`pytest` zelen". **Nije uzrokovano fazom 5** —
reproducirano na starom kodu i staroj shemi (`git stash` + `alembic downgrade`).

Lanac:
1. [db_helpers.py:17](backend/agents/db_helpers.py#L17) — `select(Concept.code, Concept.id)`
   **bez `ORDER BY`**.
2. `build_mastery_snapshot` gradi dict tim redoslijedom; `inject_mastery`
   ([prolog_engine.py:86](backend/app/prolog/prolog_engine.py#L86)) asertira Prolog fakte
   redoslijedom dicta.
3. Prolog vraća **prvo** rješenje.
4. `test_seed.py::test_seed_is_idempotent` pokreće `run_seed()` **dvaput**, a seed radi
   `on_conflict_do_update` → svaki redak `concepts` dobiva novu verziju tuplea → **fizički
   redoslijed heapa se mijenja**.

⇒ **Pokretanje `pytest`-a mijenja koncept koji preporučivač vrati živom studentu.**

Izmjereno: `inner_join` i `scalar_subquery` imaju **isti `order_index` (1)** i isti
`p_l` (0.15). U trenutnom fizičkom poretku `scalar_subquery` je ispred, pa padaju
`test_recommender_logic.py::test_advanced_recommends_inner_join` i
`test_recommender_agent.py::test_concurrent_recommends_serialized_and_correct`.
Ne ovisi o `PYTHONHASHSEED` (provjereno za 0/1/2/3/42) — dakle nije Python, nego poredak
redaka iz PostgreSQL-a.

**Nije popravljeno u 5.0**: dira Fazu 3 (`recommender_logic` / ontologija), mijenja
ponašanje preporučivača i traži zasebnu odluku. Odluka je donesena 2026-08-12 (promjena
preporuke za profil `partial` prihvaćena) i popravak je izveden na zasebnoj grani —
v. ERRATA #60.
