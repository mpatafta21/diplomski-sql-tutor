/**
 * Informacija sudionika (Faza 4.7-1a) — tekst koji student vidi PRIJE registracije.
 *
 * 🔴 OVAJ TEKST IDE U DIPLOMSKI RAD. Mijenja se svjesno i uz odluku, nikad u
 * prolazu. Izdvojen je iz `RegisterPage` upravo zato: mentor još nije potvrdio
 * traži li FOI formalni obrazac, pa jedan odlomak mora biti zamjenjiv bez
 * diranja forme, validacije ili layouta.
 *
 * KONTEKST (zašto tekst uopće postoji): evaluacija se izvodi ASINKRONO na javnom
 * URL-u, bez nadzora. Nema usmenih uputa koje bi ovo nadomjestile — ovo je
 * jedina točka kroz koju svaki sudionik prođe prije nego se prikupi ijedan
 * podatak.
 *
 * 🔴 NAMJERNO NIJE OVDJE (i ne smije se dodati bez odluke):
 *  - rok čuvanja podataka — nije određen, izmišljanje bi bila neistina
 *  - pozivanje na konkretne članke GDPR-a — nemam osnovu za takvu tvrdnju
 *  - tvrdnja o anonimnosti — username i e-adresa SE spremaju, pa bi „anonimno"
 *    bilo netočno. Pseudonimizacija se odnosi na PRIKAZ u radu, ne na pohranu.
 *  - 🔴 tvrdnja da o studentovom radu NIŠTA ne izlazi izvan sustava — od Faze 5
 *    to bi bilo netočno. Tekst upita ne izlazi, ali BROJČANI POKAZATELJI izlaze
 *    (vrsta greške, broj redaka, procjena znanja koncepta) — i to samo kad
 *    student sam zatraži savjet. Odlomak o savjetu (indeks 2) izriče granicu;
 *    ne smije se skratiti na „ništa se ne šalje" jer bi obećao više nego što
 *    sustav radi (ERRATA #59).
 *  - checkbox suglasnosti — bilježena suglasnost traži novu kolonu, dakle
 *    backend izmjenu; backend je zamrznut (🔒 errata) → Faza 5, ne 4.7.
 *    Zato je nosilac pristanka ČIN registracije, i to je izrečeno.
 */

/**
 * Kontakt za pitanja i zahtjev za brisanje podataka.
 * Potvrđeno odlukom korisnika 2026-07-26 (report gate 1).
 * Jedna izmjena ovdje mijenja sva mjesta prikaza.
 */
export const KONTAKT = "mpatafta21@student.foi.hr"

/** Naslov info bloka na `/register`. */
export const SUDJELOVANJE_NASLOV = "O sustavu i sudjelovanju"

/**
 * Odlomci info bloka, po jednoj tvrdnji — svaki je zamjenjiv pojedinačno.
 * Redoslijed je namjeran: što je → što se bilježi → što izlazi izvan sustava →
 * kako se prikazuje → dobrovoljnost → kontakt.
 */
export const SUDJELOVANJE_ODLOMCI = [
  "SQL Tutor je sustav za vježbanje SQL-a izrađen kao dio diplomskog rada na Fakultetu organizacije i informatike.",
  "Dok rješavaš zadatke, sustav bilježi tvoje SQL upite, ishode pokušaja i procjenu znanja po konceptu, vezano uz tvoj račun.",
  // 🔴 Odlomak o vanjskoj usluzi (Faza 5, ERRATA #59) — odobren tekst, mijenja se
  // samo odlukom. Stoji ODMAH iza bilježenja jer odgovara na pitanje koje to
  // bilježenje otvara: izlazi li išta od toga izvan sustava.
  //
  // 🔴 Granica je izrečena u OBA smjera i oba su provjerena mjerenjem (§A1 plana
  // 5.0): tekst upita NE izlazi, brojčani pokazatelji IZLAZE. Ne skraćivati —
  // „ne šalje se ništa" bi bilo obećanje veće od onoga što sustav radi.
  "Kad zatražiš savjet, sustav šalje vanjskoj usluzi umjetne inteligencije (Anthropic, Claude API) opis zadatka, koncept koji vježbaš, vrstu greške i njezine brojčane pokazatelje — na primjer koliko je redaka vratio tvoj upit — te procjenu tvog znanja tog koncepta. Tekst tvog upita se ne šalje. Bez zahtjeva za savjetom ništa se ne šalje izvan sustava.",
  "U diplomskom radu ti se podaci prikazuju pseudonimizirano — bez korisničkog imena i bez e-adrese.",
  // 🔴 Odlomak o roku čuvanja — odluka korisnika 2026-07-26. PODLOŽAN PROMJENI
  // ako FOI zatraži formalni obrazac informiranog pristanka: tada rok, pravna
  // osnova i način ostvarivanja prava dolaze iz obrasca, a ne odavde.
  // Ne mijenjati bez odluke — tvrdnja o brisanju je obveza prema sudioniku.
  "Podaci se čuvaju do obrane rada, nakon čega se brišu. U radu ostaje samo pseudonimizirani skup podataka bez korisničkih imena i e-adresa.",
  "Sudjelovanje je dobrovoljno i možeš prestati kad želiš. Registracijom pristaješ na sudjelovanje.",
] as const

/** Zadnji odlomak — zaseban jer nosi `KONTAKT` i renderira se s linkom. */
export const SUDJELOVANJE_KONTAKT_UVOD =
  "Za pitanja ili zahtjev za brisanje podataka:"

/**
 * Pomoćni tekst uz polje `username` na `/register`.
 *
 * 🔴 Zašto postoji: `username` se prikazuje na JAVNOJ ljestvici (4.5a — isticanje
 * trenutnog usera ide preko usernamea, jedinog polja zajedničkog `/me` i
 * `LeaderboardItem`). Student koji upiše ime i prezime izlaže ih svim ostalim
 * sudionicima, a do 4.7 mu to nigdje nije bilo rečeno.
 *
 * Formulacija je PREPORUKA, ne obećanje anonimnosti — račun i dalje nosi
 * e-adresu (vidi napomenu o pseudonimizaciji gore).
 */
export const USERNAME_POMOC =
  "Vidljivo drugim sudionicima na ljestvici — preporučujemo da ne koristiš puno ime i prezime."
