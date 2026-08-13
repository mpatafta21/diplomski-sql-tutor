# Snimke stanja hinta — DOKAZ, ne slike za rad (Faza 5.2)

🔴 **Ovo NISU figure za diplomski rad.** Figure su u `docs/figures/` i presnimljene su
jednom, 2026-08-11 (v. `docs/figures/README.md`, „Presnimavanje ide JEDNOM"). Ovaj
poddirektorij je **verifikacijski trag**: svako stanje iz §C.2 plana 5.2 uhvaćeno na
živom lancu, da tvrdnja „svih 7 stanja prikazano" ima dokaz koji netko može pogledati.

Pod verzijom su iz istog razloga kao i figure — **NALAZ #38**: artefakt koji živi u
scratchpadu nije reproducibilan i gubi se.

## Metoda

Playwright, 1280×1100, `deviceScaleFactor: 1`, snimljen **samo `Card` s editorom**
(`[data-testid="editor-box"]` → najbliži `[data-slot=card]`), ne cijeli ekran.
Datum: **2026-08-13**. Korisnik: `e2e_matrica` / `e2e_fb…` (prefiks `e2e_`, purgan
nakon snimanja — `SELECT count(*) FROM users WHERE username LIKE 'e2e_%'` → 0).

Poslužitelj: `USE_LLM_HINTS=true`, **`ANTHROPIC_API_KEY` namjerno prazan** → svi uspješni
hintovi dolaze iz kataloga (`source='fallback'`). Razlog je izbjegavanje neovlaštene
potrošnje, a gubitka dokaza nema: `source` se **nigdje ne renderira**, pa je `llm`
odgovor pikselski identičan `fallback` odgovoru. LLM put je dokazan uživo u 5.1 §E.

Dva stanja traže drugu konfiguraciju poslužitelja i snimljena su nakon restarta:
`1-hints-disabled` (`USE_LLM_HINTS=false`) i `7-hint-timeout` (`HINT_TIMEOUT=0.001`).

## Popis

| datoteka | stanje | što dokazuje |
|---|---|---|
| `1-hints-disabled.png` | 503 `hints_disabled` | gumba **nema u DOM-u** (`count() === 0`), nema ni meta retka — nije „renderiran pa sakriven" |
| `2-zakljucan-razlog.png` | zaključano | `aria-disabled="true"`, vidljiv razlog ispod reda, natpis „Zatraži hint" |
| `3-otkljucan-brojac.png` | otključano | isti natpis, brojač `Preostalo savjeta: N` — brojač NIJE u natpisu |
| `4-hint-success.png` | 200 `fallback` | tekst savjeta u slotu iznad feedbacka |
| `5-hint-unavailable.png` | 503 `hint_unavailable` | gumb **ostaje**, `ErrorState` s retryjem |
| `6a-hint-not-unlocked.png` | 409 `hint_not_unlocked` | poruka **bez** retryja (ponavljanje bi dalo isti 409) |
| `6b-hint-rate-limited.png` | 429 `hint_rate_limited` | razlog + odbrojavanje „Sljedeći savjet za 3 h 57 min" |
| `7-hint-timeout.png` | 504 `hint_timeout` | vlastita poruka, retry ponuđen |
| `8-koegzistencija-stale.png` | hint + feedback | oba vidljiva, hint **gore**, oznaka „zatražen uz prethodnu predaju" |

### Re-verifikacija `FeedbackPanel`a (dodir eval-verificiranog puta)

`TaskPage.tsx` je diran, pa su sva četiri stanja ponovno provjerena na živom lancu
(task 8, korisnik `e2e_fb…`):

| datoteka | verdikt | poruka |
|---|---|---|
| `fb-netocno.png` | Netočno | „Upit vraća krive stupce.", 0 XP |
| `fb-djelomicno.png` | Djelomično | „Skoro! Stupci su točni, ali redovi nisu.", +8 XP |
| `fb-tocno.png` | Točno | „Bravo — rezultat je točan!", +10 XP, bedž „Prvi uspjeh" |
| `fb-vec-rijeseno.png` | Točno | „Već riješeno · bez XP" |

Bez regresije.
