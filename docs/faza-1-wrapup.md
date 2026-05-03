# FAZA 1 — Wrap-up i evaluacija

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Faza:** 1 od 7 (Domenski model i baza)
**Status:** Završena 25.04.2026.
**Trajanje:** 2 tjedna planiranog rada
**Verifikacija:** 41/41 testova prolazi, sve invariante zadovoljene

---

## 1. Sažetak izvedenog rada

Faza 1 je dizajnirala i implementirala temeljnu domensku reprezentaciju sustava — što korisnici uče (30 SQL koncepata), kako je to znanje strukturirano (38 prerequisite ovisnosti, hibridni Prolog + BKT model), i kako se reprezentira u perzistentnoj memoriji (16 tablica glavne baze + 8 tablica sandbox baze s e-commerce domenom).

Sustav je razvijen u tri sub-faze:

- **Sub-faza 1A (Baza)** — SQLAlchemy modeli, Alembic migracije, seed master podataka
- **Sub-faza 1B (Prolog)** — ontologija, pravila preporuke (Zone of Proximal Development), pyswip Python ↔ Prolog bridge
- **Sub-faza 1C (Sandbox + BKT)** — sandbox e-commerce baza s Faker seed-om, Bayesian Knowledge Tracing model

## 2. Ključni doprinosi

| Doprinos | Dokaz |
|---|---|
| Defensible granulacija (30 atomskih KC-ova) | Argumentacija s citatima Mitrovic, Pelánek, Yudelson, Piech |
| Hibridni AI: simboličko + vjerojatnosno | Prolog `recommend_next/2` injecta BKT `mastery/3` činjenice u runtime |
| Empirijski validirana BKT matematika | Marko scenario test prolazi s odstupanjem < 0.003 od ručnog izračuna |
| Reproducibilan sandbox dataset | Faker seed=42, identični countovi i sample-ovi između run-ova |
| Test-driven implementacija | 41 test, 0 regresija kroz 3 sub-faze |

## 3. Verifikacija deliverables (kraj Faze 1)

### 3.1 Kvantitativni dokazi

| Metrika | Vrijednost | Source |
|---|---|---|
| SQL koncepata u Prologu | 30 | `concept/1` činjenice |
| Prerequisite rubova | 38 | `prerequisite/2` činjenice |
| Modula | 7 (1-6 + transverzalni 0) | `module_name/2` |
| Tablica glavne baze | 16 | Alembic migracija ac6a5eeac6e5 |
| Tablica sandbox baze | 8 | `ecommerce_v1` schema |
| Master master podataka u bazi | 7 modules + 30 concepts + 38 prereqs + 5 badges | Idempotentni seed |
| Sandbox seed redaka | 4 895 | 15+30+100+200+50+1000+3000+500 |
| Testova ukupno | 41 | 18 baseline + 9 BKT + 14 sandbox |

### 3.2 Sandbox invariante (ključne za Fazu 2)

| Invarianta | Cilj | Izmjereno | Status |
|---|---|---|---|
| Kupci bez narudžbi (anti-join scenarij) | ≥ 20 | 25 | ✅ |
| `orders.employee_id` NULL postotak | ~30% | 29.30% | ✅ |
| `orders.total_amount` konzistentnost | 0 mismatcha | 0 | ✅ |
| Reproducibilnost (Faker seed=42) | Identični run-ovi | Potvrđeno testom | ✅ |

### 3.3 BKT matematička validacija

Test scenarija "Marko" (hard tier, 3 pokušaja: incorrect → correct → correct):

| Pokušaj | Očekivano P(L) | Izmjereno P(L) | Odstupanje |
|---|---|---|---|
| Inicijalno | 0.0500 | 0.0500 | 0.0000 |
| Nakon 1 (netočan) | 0.107 | 0.1078 | +0.0008 |
| Nakon 2 (točan) | 0.554 | 0.5561 | +0.0021 |
| Nakon 3 (točan) | 0.922 | 0.9227 | +0.0007 |

Sva odstupanja su unutar tolerancije 0.01. Razlika potječe od rounding-a u ručnom izračunu (4 decimale između koraka); kod ne zaokružuje međurezultate, što je matematički ispravnije.

### 3.4 Git artefakti

```
faza-1a-baza            (Sub-faza 1A complete)
faza-1b-prolog          (Sub-faza 1B complete)
faza-1c-bkt-sandbox     (Sub-faza 1C complete)
faza-1-complete         (Faza 1 milestone)
```

## 4. Errata za dokument `faza-1-domenski-model.md`

Tijekom implementacije identificirana su tri minor odstupanja od originalnog dokumenta. Dokumentirana ovdje za buduće ažuriranje rada:

| # | Lokacija | Original | Ispravak | Razlog |
|---|---|---|---|---|
| 1 | §5.5 | P(L) ≈ 0.107, 0.554, 0.922 | P(L) = 0.1078, 0.5561, 0.9227 | Preciznije vrijednosti iz koda (bez int rounding-a) |
| 2 | §4.5 | `join_condition: P_L = 0.8` u `user_join_stuck` profilu | `P_L = 0.9` | Threshold 0.85 — s 0.8 prereqs_met fail | 
| 3 | §9 | "15 tablica glavne baze" | 16 tablica | Typo: `concept_prerequisites` izostavljena u checklist-i ali postoji u §6.2 DDL-u |

## 5. Tehnološki dug (rješava se prije/u Fazi 3)

| Stavka | Opis | Rok | Težina |
|---|---|---|---|
| Sandbox role login | `sandbox_readonly` i `sandbox_readwrite` su NOLOGIN. Faza 3 EvaluatorAgent koristit će `SET ROLE` pattern (logiran kao app user, runtime switch) — preferred jer nema lozinke za sandbox role-ove | Faza 3 | Low |
| `relationship` ORM veze u SQLAlchemy | Importirano u models.py ali ne korišteno (čeka da Faza 3 doda joinove) | Faza 3 | Low |
| `tier(insert, easy)` | Plan ga je tako klasificirao. Nakon Faze 2 (kad vidimo distribuciju zadataka), revidirati prema empirici | Faza 2 | Low |

## 6. Spremnost za Fazu 2

Fazu 2 (generator SQL zadataka kroz Anthropic Claude API) blokirale bi sljedeće stvari iz Faze 1; sve su završene:

- [x] Postoji `tasks` tablica s JSONB `expected_result` — generator će ovdje pisati
- [x] Postoji `task_concepts` M:N veza — generator će označavati koje koncepte zadatak pokriva
- [x] Postoji `concept` Prolog činjenica za sve 30 KC-ova — generator referira po `code`-u
- [x] Sandbox `ecommerce_v1` schema postoji s 4895 reproducibilnih redaka — testiranje očekivanih rezultata
- [x] Postoji `is_active` flag na `tasks` — generirani zadaci koji ne prođu validaciju mogu biti deaktivirani

## 7. Reflektivne napomene

**Što je dobro funkcioniralo:**
- Podjela na 3 sub-faze — zero context overflow, jasna entry/exit kriterija po sub-fazi
- TDD pristup u 1B i 1C — testovi su uhvatili rounding bug u BKT-u prije nego što je došao u dokument
- Code review skill nakon kritičnih taskova — uhvatio fail-safe ordering bug u `PrologEngine.__init__`

**Što treba pamtiti za buduće faze:**
- Dokumenti **prije** koda funkcioniraju — Faza 1 dokument je bio source of truth, smanjio je broj decision iteracija
- Empirijska validacija matematičkih modela (Marko test) je obavezna — bez nje BKT bi se mogao kompilirati ali davati pogrešne rezultate
- Faker seed za reproducibilnost je **must** za testove — bez fiksnog seed-a, sandbox testovi su flaky

---

*Faza 1 zaključena 25.04.2026. Sljedeći korak: Faza 2 — generiranje 80+ SQL zadataka uz Claude API i ručna validacija.*
