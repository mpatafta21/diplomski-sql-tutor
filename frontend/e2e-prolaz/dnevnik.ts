/**
 * Dnevnik prolaza — trajno stanje i zapis događaja.
 *
 * 🔴 Zašto uopće postoji stanje na disku: prolaz NE VRAĆA bazu na baseline
 * (podaci ostaju kao materijal za rad), pa ponovno pokretanje iz nule ne bi
 * bilo „ponovi test" nego „udvostruči podatke". Stanje omogućuje NASTAVAK:
 * skripta se prijavi na postojeći račun i preskoči zadatke koji su već gotovi.
 *
 * Sve se piše ODMAH nakon svakog događaja (`writeFileSync`, bez buffera) — pad
 * usred prolaza ne smije progutati ono što se već dogodilo u bazi.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const OVDJE = dirname(fileURLToPath(import.meta.url))
/** `PROLAZ_STANJE` odvaja probni prolaz od stvarnog — probni ne smije ostaviti
 *  stanje koje bi stvarni prolaz pročitao kao „nastavak". */
export const STANJE_DIR = process.env.PROLAZ_STANJE ?? join(OVDJE, ".stanje")
const STANJE_FILE = join(STANJE_DIR, "stanje.json")

/** Jedan planiran pokušaj (iz `plan.json`). */
export interface PlanPokusaj {
  mutacija: string | null
  opis: string
  query: string
  error_type: string | null
  is_correct: boolean
  namjera: "netocno" | "tocno" | "sonda"
  ocekivano: string
}

/** Jedan zadatak u planu prolaza. */
export interface PlanZadatak {
  task_id: number
  koncept: string
  tier: string
  modul: number
  difficulty: number
  naslov: string
  /** 0 = točno iz prve, 1 = jedna netočna, 2 = dvije netočne. */
  profil: number
  /** Je li na ovom zadatku planiran zahtjev za savjetom. */
  hint: boolean
  pokusaji: PlanPokusaj[]
}

/** Jedna predaja kroz sučelje — jedan redak buduće SEKVENCA tablice. */
export interface Predaja {
  redni: number
  ts: string
  task_id: number
  koncept: string | null
  modul: number
  tier: string
  difficulty: number
  naslov: string
  /** Kako je student došao na ovaj zadatak. */
  navigacija: string
  /** Reason preporuke koja je dovela na ovaj zadatak (null za prvi/module klik). */
  dolazni_reason: string | null
  pokusaj_br: number
  mutacija: string | null
  opis_greske: string | null
  sql: string
  ocekivano: string
  /** Ono što je sučelje stvarno prikazalo. */
  verdict: string
  is_correct: boolean | null
  error_type: string | null
  detail: string | null
  xp: number
  xp_delta: number
  level: number
  current_streak: number
  new_badges: string[]
  already_solved: boolean
  rec_task_id: number | null
  rec_concept: string | null
  rec_reason: string | null
  /** Trajanje POST /attempt mjereno u pregledniku (ms). */
  trajanje_ms: number
}

export interface HintZapis {
  redni: number
  ts: string
  task_id: number
  naslov: string
  koncept: string | null
  tier: string
  difficulty: number
  /** Studentov upit koji je prethodio savjetu. */
  sql: string
  error_type: string
  /** Doslovni tekst savjeta, onako kako ga student vidi. */
  tekst: string
  /** llm | fallback — iz odgovora rute. */
  izvor: string | null
  /** Ako savjet nije stigao: detail rute (hint_no_catalog, …). */
  neuspjeh: string | null
  preostalo_prije: number | null
  preostalo_poslije: number | null
}

export interface Dogadaj {
  ts: string
  vrsta: string
  poruka: string
  podaci?: Record<string, unknown>
}

export interface Stanje {
  korisnik: string
  email: string
  lozinka: string
  pokrenuto: string
  faza: "preporucivac" | "moduli"
  /** task_id-evi koji su u OVOM prolazu dovedeni do točnog rješenja. */
  gotovi: number[]
  /** task_id-evi koji su obrađeni ali NISU riješeni (plan nije uspio). */
  preskoceni: number[]
  predaje: Predaja[]
  hintovi: HintZapis[]
  dogadaji: Dogadaj[]
  snimke: string[]
}

function prazno(korisnik: string, email: string, lozinka: string): Stanje {
  return {
    korisnik,
    email,
    lozinka,
    pokrenuto: new Date().toISOString(),
    faza: "preporucivac",
    gotovi: [],
    preskoceni: [],
    predaje: [],
    hintovi: [],
    dogadaji: [],
    snimke: [],
  }
}

export class Dnevnik {
  stanje: Stanje
  /** true kad je stanje učitano s diska (nastavak), false za svjež prolaz. */
  readonly nastavak: boolean

  constructor(korisnik: string, email: string, lozinka: string) {
    if (!existsSync(STANJE_DIR)) mkdirSync(STANJE_DIR, { recursive: true })
    if (existsSync(STANJE_FILE)) {
      this.stanje = JSON.parse(readFileSync(STANJE_FILE, "utf-8")) as Stanje
      this.nastavak = true
    } else {
      // 🔴 NE PIŠE se ovdje. Playwright učita spec DVAPUT (jednom da prebroji
      // testove, jednom u workeru da ih pokrene); zapis u konstruktoru bi drugo
      // učitavanje uvjerio da je riječ o nastavku prekinutog prolaza.
      // Datoteka nastaje pri prvom stvarnom događaju, dakle unutar testa.
      this.stanje = prazno(korisnik, email, lozinka)
      this.nastavak = false
    }
  }

  spremi(): void {
    writeFileSync(STANJE_FILE, JSON.stringify(this.stanje, null, 1), "utf-8")
  }

  zapisi(vrsta: string, poruka: string, podaci?: Record<string, unknown>): void {
    this.stanje.dogadaji.push({
      ts: new Date().toISOString(),
      vrsta,
      poruka,
      podaci,
    })
    this.spremi()
    console.log(`   · [${vrsta}] ${poruka}`)
  }

  dodajPredaju(p: Omit<Predaja, "redni" | "ts">): Predaja {
    const zapis: Predaja = {
      redni: this.stanje.predaje.length + 1,
      ts: new Date().toISOString(),
      ...p,
    }
    this.stanje.predaje.push(zapis)
    this.spremi()
    return zapis
  }

  dodajHint(h: Omit<HintZapis, "redni" | "ts">): HintZapis {
    const zapis: HintZapis = {
      redni: this.stanje.hintovi.length + 1,
      ts: new Date().toISOString(),
      ...h,
    }
    this.stanje.hintovi.push(zapis)
    this.spremi()
    return zapis
  }

  oznaciGotov(taskId: number): void {
    if (!this.stanje.gotovi.includes(taskId)) {
      this.stanje.gotovi.push(taskId)
      this.spremi()
    }
  }

  preskoci(taskId: number): void {
    if (!this.stanje.preskoceni) this.stanje.preskoceni = []
    if (!this.stanje.preskoceni.includes(taskId)) {
      this.stanje.preskoceni.push(taskId)
      this.spremi()
    }
  }

  jeGotov(taskId: number): boolean {
    return this.stanje.gotovi.includes(taskId)
  }

  snimkaZabiljezena(ime: string): boolean {
    return this.stanje.snimke.includes(ime)
  }

  zabiljeziSnimku(ime: string): void {
    if (!this.stanje.snimke.includes(ime)) {
      this.stanje.snimke.push(ime)
      this.spremi()
    }
  }
}
