# Skill: bkt-math-check

**Status: TODO — implementirati u Fazi 3**

## Svrha

Ovaj skill se koristi u Fazi 3 (BKT implementacija) za verifikaciju da BKT matematika
radi ispravno. Provjerava:
- Jesu li BKT parametri u validnim rasponima [0,1]
- Je li posterior update formula ispravno implementirana
- Jesu li rubni slučajevi (P(L)→1, P(L)→0) ispravno obrađeni
- Konzistentnost s inicijalnim parametrima iz CLAUDE.md

## Inicijalni parametri (iz CLAUDE.md)

```
P(L₀) = 0.1   # Inicijalna vjerojatnost znanja
P(T)  = 0.2   # Vjerojatnost tranzicije (učenja)
P(G)  = 0.2   # Vjerojatnost pogađanja (guess)
P(S)  = 0.1   # Vjerojatnost pogreške (slip)
```

## BKT formula koju treba provjeriti

```
# Posterior update:
P(Ln | correct) = P(Ln-1) * (1 - P(S)) / [P(Ln-1) * (1 - P(S)) + (1 - P(Ln-1)) * P(G)]
P(Ln | incorrect) = P(Ln-1) * P(S) / [P(Ln-1) * P(S) + (1 - P(Ln-1)) * (1 - P(G))]

# Tranzicija:
P(Ln+1) = P(Ln) + (1 - P(Ln)) * P(T)
```

## Kada koristiti

Koristiti nakon implementacije `backend/bkt/` modula i pri svakoj promjeni BKT logike.

## Napomene za implementaciju

- Pisati property-based testove (hypothesis library) za rubne slučajeve
- Usporediti s referentnom implementacijom (paper: Corbett & Anderson 1994)
