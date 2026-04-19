# /status — Stanje cijelog sustava

Pokreni sve potrebne provjere stanja sustava i prikaži rezultate.

## Komande

```bash
echo "=== Docker servisi ==="
docker compose ps

echo ""
echo "=== Git status ==="
git status --short

echo ""
echo "=== Prosody registrirani korisnici/agenti ==="
docker exec diplomski-prosody prosodyctl list-users localhost 2>/dev/null || \
docker exec $(docker ps --filter "name=prosody" --format "{{.Names}}" | head -1) prosodyctl list-users localhost 2>/dev/null || \
echo "(Prosody kontejner nije pokrenut ili nije dostupan)"

echo ""
echo "=== PostgreSQL — main baza ==="
docker exec $(docker ps --filter "name=postgres_main" --format "{{.Names}}" | head -1) psql -U postgres -c "\l" 2>/dev/null || \
echo "(PostgreSQL main nije dostupan)"
```
