"""
pyswip smoke test — provjerava da Python može pozvati Prolog pravila.
"""
from pyswip import Prolog

prolog = Prolog()
prolog.consult("prolog/test_ontology.pl")

print("=== Svi koncepti ===")
for result in prolog.query("concept(X)"):
    print(f"  - {result['X']}")

print("\n=== Što Marko može sljedeće učiti? ===")
for result in prolog.query("can_learn(marko, X)"):
    print(f"  ✓ {result['X']}")

print("\n=== Ovisnosti LEFT JOIN ===")
for result in prolog.query("prerequisite(left_join, X)"):
    print(f"  left_join zahtijeva: {result['X']}")
