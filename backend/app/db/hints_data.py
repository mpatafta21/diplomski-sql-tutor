"""Katalog hintova (Faza 5.0, sekcija C) — 32 retka, top 8 koncepata × 4 tipa greške.

🔴 `hints` je READ-ONLY u runtimeu (H2.2a). Ovo je JEDINI izvor koji ga puni; izlaz
LLM-a se NIKAD ne upisuje ovamo. Redak služi kao `fallback` kad LLM nije dostupan.

🔴 Redoslijed: `row_mismatch` × koncept ide PRVI (H3.2). Ondje hint vrijedi najviše —
student ima točne stupce i najbliže je rješenju, a djelomičan pokušaj se za
otključavanje hinta broji kao netočan.

Kriterij prihvaćanja (§G5.4), mehanički provjeren u `tests/test_hints_seed.py`:
  1. tekst imenuje SQL konstrukt ili pravilo vezano uz koncept (v. `CONCEPT_TERMS`),
  2. nije parafraza `ERROR_TEXT[error_type]` iz `frontend/src/lib/feedback.ts`,
  3. ne sadrži `expected_query` ni vrijednost iz `expected_result` ijednog zadatka
     tog koncepta (guard §G2.3).

Hintovi navode na rješenje, ne daju ga.
"""

from __future__ import annotations

#: Top 8 koncepata po zastupljenosti u katalogu zadataka.
TOP_CONCEPTS = (
    "group_by",
    "multi_table_join",
    "agg_count",
    "delete",
    "having_filter",
    "inner_join",
    "null_handling",
    "update",
)

#: Četiri koncept-ovisna tipa greške. `syntax_error` (prazan editor), `timeout` i
#: `unsupported_eval` NISU ovdje — njihov uzrok nema veze s konceptom zadatka.
CONCEPT_ERROR_TYPES = (
    "row_mismatch",
    "empty_result",
    "wrong_columns",
    "execution_error",
)

#: Pojmovi koji dokazuju da hint govori o KONCEPTU, a ne o tipu greške općenito.
#: Svaki `hint_text` mora sadržavati barem jedan pojam svog koncepta (case-insensitive).
CONCEPT_TERMS: dict[str, tuple[str, ...]] = {
    "group_by": ("GROUP BY",),
    "multi_table_join": ("JOIN",),
    "agg_count": ("COUNT",),
    "delete": ("DELETE",),
    "having_filter": ("HAVING",),
    "inner_join": ("JOIN",),
    "null_handling": ("NULL", "COALESCE"),
    "update": ("UPDATE", "SET"),
}

#: (error_type, concept_code, hint_text). `row_mismatch` blok je namjerno prvi.
HINTS: tuple[tuple[str, str, str], ...] = (
    # ---------------------------------------------------------------- row_mismatch
    (
        "row_mismatch",
        "group_by",
        "Stupci su na mjestu, pa je pitanje po čemu grupiraš. Provjeri je li u "
        "GROUP BY točno onaj skup stupaca koji određuje jednu skupinu — svaki "
        "dodatni stupac usitnjava skupine, a svaki izostavljen ih stapa.",
    ),
    (
        "row_mismatch",
        "multi_table_join",
        "Kod spajanja triju ili više tablica broj redaka gotovo uvijek otkriva "
        "uvjet spajanja. Provjeri ima li svaki JOIN svoj ON s ispravnim parom "
        "ključeva — jedan uvjet koji nedostaje umnaža retke kartezijevim produktom.",
    ),
    (
        "row_mismatch",
        "agg_count",
        "COUNT(*) broji retke, COUNT(stupac) preskače nedostajuće vrijednosti, a "
        "COUNT(DISTINCT stupac) broji različite. Provjeri koju od te tri stvari "
        "zadatak zapravo traži.",
    ),
    (
        "row_mismatch",
        "delete",
        "Zahvaćen je krivi broj redaka — pogledaj uvjet u DELETE naredbi. Preširok "
        "uvjet briše previše, prestrog premalo; najbrže ga provjeriš tako da isti "
        "WHERE prvo pustiš kroz SELECT.",
    ),
    (
        "row_mismatch",
        "having_filter",
        "HAVING filtrira skupine nakon agregacije, WHERE pojedinačne retke prije "
        "nje. Ako je broj skupina krivi, provjeri je li tvoj uvjet završio u pravoj "
        "od te dvije klauzule.",
    ),
    (
        "row_mismatch",
        "inner_join",
        "INNER JOIN zadržava samo retke koji imaju par u obje tablice. Ako ih je "
        "previše, uvjet u ON je preslab; ako premalo, spajaš po stupcu koji nema "
        "odgovarajuće vrijednosti u drugoj tablici.",
    ),
    (
        "row_mismatch",
        "null_handling",
        "Nedostajuća vrijednost nije vrijednost nego njezina odsutnost, pa "
        "usporedba = NULL nikad nije istinita. Provjeri koristiš li IS NULL "
        "odnosno IS NOT NULL ondje gdje treba.",
    ),
    (
        "row_mismatch",
        "update",
        "UPDATE je promijenio krivi broj redaka — provjeri uvjet. Bez WHERE se "
        "mijenja cijela tablica; opseg promjene provjeri tako da isti uvjet prvo "
        "pustiš kroz SELECT.",
    ),
    # ---------------------------------------------------------------- empty_result
    (
        "empty_result",
        "group_by",
        "Grupiranje ne može proizvesti skupinu ni iz čega. Ako je ispis prazan, "
        "filtar koji se izvodi prije GROUP BY već je odsjekao sve retke — provjeri "
        "WHERE prije nego dirati grupiranje.",
    ),
    (
        "empty_result",
        "multi_table_join",
        "U lancu JOIN-ova dovoljno je da jedan uvjet spajanja ne pogodi nijedan par "
        "pa cijeli ispis ostane prazan. Provjeravaj lanac tako da tablice dodaješ "
        "jednu po jednu.",
    ),
    (
        "empty_result",
        "agg_count",
        "COUNT nad praznim skupom vraća nulu, ali uz GROUP BY ne vraća nijedan "
        "redak — nema skupine koju bi izbrojio. Provjeri je li grupiranje ovdje "
        "uopće potrebno.",
    ),
    (
        "empty_result",
        "delete",
        "DELETE sam po sebi ne vraća retke. Provjeri traži li zadatak stanje "
        "tablice nakon brisanja i pogađa li tvoj uvjet ijedan postojeći redak.",
    ),
    (
        "empty_result",
        "having_filter",
        "HAVING se primjenjuje na već izračunate agregate. Prazan ispis znači da "
        "nijedna skupina ne zadovoljava prag — provjeri granicu i operator "
        "usporedbe u uvjetu.",
    ),
    (
        "empty_result",
        "inner_join",
        "INNER JOIN izbacuje sve što nema par, pa prazan ispis obično znači da "
        "spajaš po stupcima koji ne dijele vrijednosti. Provjeri koji je stupac "
        "strani, a koji primarni ključ.",
    ),
    (
        "empty_result",
        "null_handling",
        "Uvjet nad stupcem koji sadrži NULL tiho izbacuje te retke — usporedba s "
        "nepoznatim ne daje istinu. Provjeri treba li ti IS NULL ili COALESCE.",
    ),
    (
        "empty_result",
        "update",
        "UPDATE ne vraća retke. Ako ništa ne vidiš, provjeri traži li zadatak i "
        "ispis stanja nakon promjene te pogađa li uvjet ijedan redak.",
    ),
    # --------------------------------------------------------------- wrong_columns
    (
        "wrong_columns",
        "group_by",
        "Uz GROUP BY u ispisu smiju stajati samo stupci po kojima grupiraš i "
        "agregatne funkcije. Provjeri i nazive — zadatak traži točno određena imena "
        "stupaca, pa im daj alias kroz AS.",
    ),
    (
        "wrong_columns",
        "multi_table_join",
        "Kad JOIN spoji više tablica, isti naziv stupca postoji u nekoliko njih. "
        "Kvalificiraj svaki stupac aliasom tablice i navedi izrijekom one koje "
        "zadatak traži.",
    ),
    (
        "wrong_columns",
        "agg_count",
        "Rezultatu funkcije COUNT bez aliasa PostgreSQL sam dodjeljuje ime. "
        "Provjeri traži li zadatak drukčiji naziv i dodijeli ga kroz AS.",
    ),
    (
        "wrong_columns",
        "delete",
        "DELETE nema listu stupaca — ako se stupci uspoređuju, provjerava se stanje "
        "tablice nakon brisanja. Provjeri koje stupce taj ispis treba vratiti.",
    ),
    (
        "wrong_columns",
        "having_filter",
        "Agregat po kojem filtriraš u HAVING ne mora biti i u ispisu, ni obrnuto. "
        "Provjeri koje stupce zadatak traži da se prikažu, neovisno o uvjetu.",
    ),
    (
        "wrong_columns",
        "inner_join",
        "Nakon INNER JOIN obje tablice donose svoje stupce. Umjesto zvjezdice "
        "navedi izrijekom one koje zadatak traži i kvalificiraj ih aliasom tablice.",
    ),
    (
        "wrong_columns",
        "null_handling",
        "Funkcije poput COALESCE mijenjaju naziv stupca u ispisu ako mu ne daš "
        "alias. Provjeri traži li zadatak izvorni naziv stupca.",
    ),
    (
        "wrong_columns",
        "update",
        "UPDATE mijenja podatke, a ne popis stupaca u ispisu. Provjeri koje "
        "stupce traži SELECT kojim se promjena provjerava i kojim su "
        "redoslijedom navedeni.",
    ),
    # ------------------------------------------------------------- execution_error
    (
        "execution_error",
        "group_by",
        "PostgreSQL traži da svaki stupac iz ispisa koji nije agregat bude naveden "
        "i u GROUP BY. Poruka koja spominje tu klauzulu znači da jedan stupac "
        "ondje nedostaje.",
    ),
    (
        "execution_error",
        "multi_table_join",
        "Kod više tablica greška je najčešće dvosmislen ili nepostojeći stupac — "
        "isto ime postoji u dvije tablice u JOIN-u. Dodijeli svakoj tablici alias "
        "i kvalificiraj svaki stupac njime.",
    ),
    (
        "execution_error",
        "agg_count",
        "Agregatna funkcija poput COUNT ne smije stajati u WHERE klauzuli. Uvjet "
        "nad agregatom ide u HAVING, dakle nakon grupiranja.",
    ),
    (
        "execution_error",
        "delete",
        "DELETE traži FROM i jednu tablicu, bez liste stupaca. Provjeri i "
        "uspoređuje li uvjet vrijednosti istog tipa kao stupac.",
    ),
    (
        "execution_error",
        "having_filter",
        "Uvjet u HAVING mora biti agregat; običan stupac ondje PostgreSQL odbija "
        "osim ako je i u GROUP BY. Provjeri što točno uspoređuješ.",
    ),
    (
        "execution_error",
        "inner_join",
        "JOIN bez ON klauzule PostgreSQL odbija. Provjeri i jesu li nazivi tablica "
        "i stupaca u uvjetu spajanja točno napisani.",
    ),
    (
        "execution_error",
        "null_handling",
        "Odsutnost vrijednosti ne provjerava se operatorima = i <>, nego kroz "
        "IS NULL. Provjeri i tip stupca, jer usporedba teksta i broja diže grešku.",
    ),
    (
        "execution_error",
        "update",
        "UPDATE traži SET s parovima oblika stupac = vrijednost. Provjeri i "
        "odgovara li vrijednost tipu stupca koji mijenjaš.",
    ),
)
