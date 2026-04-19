---
name: sql-task-validator
description: Validira AI-generirane SQL zadatke — provjera sintakse, konzistentnosti s Prolog ontologijom i točnosti expected_output-a na sandbox bazi.
---

# Skill: sql-task-validator

**Status: TODO — implementirati u Fazi 2**

## Svrha

Ovaj skill se koristi kada Claude AI generira nove SQL zadatke (Faza 2) da bi validirao:
- Je li generiran SQL zadatak sintaktički ispravan
- Je li zadatak konzistentan s Prolog ontologijom (ovisnosti koncepata)
- Je li expected_output točan za danu shemu sandbox baze
- Pripada li zadatak ispravnoj težinskoj kategoriji (easy/medium/hard)

## Kada koristiti

Koristiti **uvijek** nakon poziva LLM-a za generiranje zadatka, **prije** nego što se zadatak spremi u bazu.

## Ulazi (budući)

- SQL zadatak (statement + expected_output + koncepti)
- Sandbox baza konekcija
- Prolog ontologija stanje

## Izlazi (budući)

- `valid: bool`
- `errors: list[str]`
- `warnings: list[str]`

## Napomene za implementaciju

- Izvršavati SQL na sandbox bazi s read-only userom
- Usporediti s expected_output (set comparison, ne string comparison)
- Koristiti `backend/sandbox/` modul za izvršavanje
