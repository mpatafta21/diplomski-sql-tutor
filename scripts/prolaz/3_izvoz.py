"""KORAK 3: izvoz podataka prolaza u CSV za diplomski rad.

Spaja DVA izvora, i to namjerno:
  * `frontend/e2e-prolaz/.stanje/stanje.json` — ono što je SUČELJE prikazalo i
    koliko je odgovor trajao MJERENO U PREGLEDNIKU (jedino mjesto gdje to
    postoji; baza pamti trajanje izvrsavanja upita, ne trajanje odgovora);
  * `tutor_main` — BKT povijest, XP dnevnik i bedzevi, dakle ono sto je sustav
    doista zapisao.

Pokreni::

    python3 scripts/prolaz/3_izvoz.py

Izlaz: `docs/prolaz-podaci/*.csv`
"""

from __future__ import annotations

import csv
import json
import statistics
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
STANJE = _REPO / "frontend" / "e2e-prolaz" / ".stanje" / "stanje.json"
IZLAZ = _REPO / "docs" / "prolaz-podaci"
KORISNIK = "Maks"

# ---------------------------------------------------------------------------
# 🔴 OCJENE SAVJETA — prosudba analiticara, ne podatak iz sustava.
#
# Stoje ovdje, a ne u bazi, upravo zato sto su prosudba: sustav ne zna je li
# savjet tocan. Kriterij je jedan i doslovan: **opisuje li savjet gresku koju je
# student STVARNO napravio**. Obrazlozenja su u
# `docs/e2e-kompletan-prolaz-wrapup.md`, §Savjeti.
# ---------------------------------------------------------------------------
OCJENE = {
    1: (
        "TOCAN I KORISTAN",
        "Imenuje tocno klauzulu koja nedostaje (GROUP BY). Ne tvrdi nista o "
        "sadrzaju studentova upita, pa nema sto ni promasiti.",
    ),
    2: (
        "NETOCAN",
        "Student je pogrijesio SMJER SORTIRANJA (ASC umjesto DESC). Savjet "
        "objasnjava HAVING vs WHERE i GROUP BY — oboje je student vec napisao "
        "ispravno. Diagnoza opisuje gresku koje nema.",
    ),
    3: (
        "TOCAN I KORISTAN",
        "Imenuje tocan anti-obrazac (CAST nad stupcem ponistava indeks) i tocnu "
        "posljedicu u planu (Hash Join umjesto Nested Loop).",
    ),
    4: (
        "TOCAN I KORISTAN",
        "Imenuje stupac koji nedostaje (`distinct_products_sold`) i upucuje na "
        "aliase agregata. Uzrok pripisuje i 'redoslijedu', sto nije tocno, ali "
        "cilj je pogodjen.",
    ),
    5: (
        "DJELOMICNO TOCAN",
        "Prva recenica je tocna i utemeljena u detalju ('vraca vise redaka nego "
        "sto bi trebalo'). Ostatak nagadja kvar u koreliranome podupitu, koji je "
        "student napisao ispravno — greska je bila LIMIT 7 umjesto 5.",
    ),
    6: (
        "ISPRAVNO ODBIJEN",
        "Nije savjet nego odbijanje: kredit je potrosen. Poruka je tocna, nosi "
        "vrijeme dopune i NE trosi kredit (izmjereno 0 -> 0).",
    ),
}


def psql(sql: str) -> list[list[str]]:
    out = subprocess.run(
        [
            "docker", "compose", "exec", "-T", "postgres-main",
            "psql", "-U", "tutor", "-d", "tutor_main", "-F", "\x1f", "-A", "-qtc", sql,
        ],
        cwd=_REPO, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return [r.split("\x1f") for r in out.split("\n") if r]


def zapisi(ime: str, zaglavlje: list[str], retci: list[list]) -> None:
    put = IZLAZ / ime
    with open(put, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(zaglavlje)
        w.writerows(retci)
    print(f"  ✓ {ime:<28} {len(retci):>4} redaka")


def main() -> None:
    IZLAZ.mkdir(parents=True, exist_ok=True)
    stanje = json.loads(STANJE.read_text(encoding="utf-8"))
    predaje = stanje["predaje"]

    # ── a) SEKVENCA ────────────────────────────────────────────────────────
    zapisi(
        "a-sekvenca.csv",
        ["redni", "vrijeme", "zadatak", "koncept", "modul", "tier", "tezina",
         "naslov", "navigacija", "reason_preporuke_koja_je_dovela",
         "pokusaj_br", "greska_studenta", "opis_greske", "verdikt",
         "error_type", "detail", "xp_delta", "xp_ukupno", "level",
         "streak", "novi_bedzevi", "preporuka_task", "preporuka_koncept",
         "preporuka_reason", "trajanje_ms"],
        [[p["redni"], p["ts"], p["task_id"], p["koncept"], p["modul"], p["tier"],
          p["difficulty"], p["naslov"], p["navigacija"], p["dolazni_reason"],
          p["pokusaj_br"], p["mutacija"] or "", p["opis_greske"] or "",
          p["verdict"], p["error_type"] or "", (p["detail"] or "").replace("\n", " ⏎ "),
          p["xp_delta"], p["xp"], p["level"], p["current_streak"],
          ";".join(p["new_badges"]), p["rec_task_id"], p["rec_concept"],
          p["rec_reason"], p["trajanje_ms"]] for p in predaje],
    )

    # ── b) BKT ─────────────────────────────────────────────────────────────
    bkt = psql(f"""
        SELECT h.id, h.created_at, c.code, m.number, h.p_l, h.attempt_id,
               a.task_id, a.is_correct, coalesce(a.error_type,''), a.attempt_number
        FROM skill_mastery_history h
        JOIN concepts c ON c.id = h.concept_id
        JOIN modules m ON m.id = c.module_id
        LEFT JOIN attempts a ON a.id = h.attempt_id
        WHERE h.user_id = (SELECT id FROM users WHERE username = '{KORISNIK}')
        ORDER BY h.id
    """)
    # Redni broj tocke PO KONCEPTU — os x krivulje u radu.
    brojac: dict[str, int] = {}
    retci = []
    for r in bkt:
        brojac[r[2]] = brojac.get(r[2], 0) + 1
        retci.append([r[0], r[1], r[2], r[3], r[4], brojac[r[2]], r[5], r[6], r[7], r[8], r[9]])
    zapisi(
        "b-bkt-krivulje.csv",
        ["id", "vrijeme", "koncept", "modul", "p_l", "tocka_u_krivulji",
         "attempt_id", "zadatak", "attempt_tocan", "attempt_error_type",
         "attempt_number"],
        retci,
    )

    # ── c) XP / LEVEL / BEDZEVI ────────────────────────────────────────────
    xp = psql(f"""
        SELECT x.id, x.created_at, x.delta, x.reason, x.attempt_id,
               coalesce(a.task_id::text,''), coalesce(a.is_correct::text,'')
        FROM xp_log x
        LEFT JOIN attempts a ON a.id = x.attempt_id
        WHERE x.user_id = (SELECT id FROM users WHERE username = '{KORISNIK}')
        ORDER BY x.id
    """)
    kum, prosli_level, retci = 0, 1, []
    for r in xp:
        kum += int(r[2])
        level = 1 + kum // 100          # gamification_logic.LEVEL_STEP = 100
        retci.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], kum, level,
                      "DA" if level > prosli_level else ""])
        prosli_level = level
    zapisi(
        "c-xp-level.csv",
        ["id", "vrijeme", "delta", "razlog", "attempt_id", "zadatak",
         "attempt_tocan", "xp_kumulativno", "level", "level_up"],
        retci,
    )

    bedzevi = psql(f"""
        SELECT b.code, b.name, ub.earned_at
        FROM user_badges ub JOIN badges b ON b.id = ub.badge_id
        WHERE ub.user_id = (SELECT id FROM users WHERE username = '{KORISNIK}')
        ORDER BY ub.earned_at
    """)
    zapisi("c-bedzevi.csv", ["kod", "naziv", "osvojen"], bedzevi)

    # ── d) SAVJETI ─────────────────────────────────────────────────────────
    plan = json.loads(
        (_REPO / "frontend" / "e2e-prolaz" / "plan.json").read_text(encoding="utf-8")
    )
    retci = []
    for h in stanje["hintovi"]:
        z = plan["zadaci"][str(h["task_id"])]
        ocjena, obrazlozenje = OCJENE.get(h["redni"], ("", ""))
        retci.append([
            h["redni"], h["ts"], h["task_id"], h["naslov"], h["koncept"],
            h["tier"], h["difficulty"], h["error_type"], h["izvor"] or "",
            h["neuspjeh"] or "", h["preostalo_prije"], h["preostalo_poslije"],
            h["sql"], z["pokusaji"][-1]["query"], h["tekst"], ocjena, obrazlozenje,
        ])
    zapisi(
        "d-hintovi.csv",
        ["redni", "vrijeme", "zadatak", "naslov", "koncept", "tier", "tezina",
         "error_type", "izvor", "neuspjeh", "kredit_prije", "kredit_poslije",
         "upit_studenta", "tocno_rjesenje", "tekst_savjeta", "ocjena",
         "obrazlozenje_ocjene"],
        retci,
    )

    # ── f) DNEVNIK DOGADAJA ────────────────────────────────────────────────
    # Sirovo stanje prolaza (`.stanje/`) je gitignorirano jer je promjenjivo;
    # dogadaji su jedini njegov dio koji ne zavrsi ni u jednom drugom CSV-u, pa
    # se izvoze da se ne izgube.
    zapisi(
        "f-dogadaji.csv",
        ["vrijeme", "vrsta", "poruka", "podaci"],
        [[e["ts"], e["vrsta"], e["poruka"],
          json.dumps(e.get("podaci"), ensure_ascii=False) if e.get("podaci") else ""]
         for e in stanje["dogadaji"]],
    )

    # ── e) VREMENA ─────────────────────────────────────────────────────────
    # 🔴 Negativna trajanja se IZDVAJAJU, ne brisu tiho: nastaju kad sistemski
    # sat skoci unatrag (WSL2 + NTP korekcija) izmedju t0 i odgovora. Broj im je
    # vidljiv u sazetku — mjerenje koje se odbacuje mora se barem prebrojati.
    sva = [p["trajanje_ms"] for p in predaje]
    valjana = sorted(t for t in sva if t >= 0)
    odbacena = [t for t in sva if t < 0]

    def kvantil(q: float) -> float:
        return statistics.quantiles(valjana, n=100)[q - 1] if len(valjana) > 1 else valjana[0]

    zapisi(
        "e-vremena.csv",
        ["redni", "zadatak", "koncept", "error_type", "trajanje_ms", "valjano"],
        [[p["redni"], p["task_id"], p["koncept"], p["error_type"] or "correct",
          p["trajanje_ms"], "da" if p["trajanje_ms"] >= 0 else "ne"] for p in predaje],
    )

    sazetak = {
        "korisnik": KORISNIK,
        "predaja_ukupno": len(predaje),
        "zadataka_rijeseno": len(stanje["gotovi"]),
        "savjeta_zatrazeno": len(stanje["hintovi"]),
        "xp_zavrsni": predaje[-1]["xp"],
        "level_zavrsni": predaje[-1]["level"],
        "vremena_ms": {
            "N": len(valjana),
            "odbacenih_negativnih": len(odbacena),
            "min": valjana[0],
            "p50": round(statistics.median(valjana), 1),
            "p95": round(kvantil(95), 1),
            "max": valjana[-1],
            "napomena": "N=1 student, sekvencijalno, bez konkurencije; "
                        "mjereno u pregledniku od klika na Submit do odgovora.",
        },
        "bkt_tocaka": len(bkt),
        "xp_zapisa": len(xp),
        "bedzeva": len(bedzevi),
    }
    (IZLAZ / "sazetak.json").write_text(
        json.dumps(sazetak, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"  ✓ {'sazetak.json':<28}")
    print()
    print(json.dumps(sazetak["vremena_ms"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
