#!/usr/bin/env bash
#
# Backup baze `tutor_main` IZVAN docker volumena + VERIFIKACIJA RESTORE-a.
#
# Zašto postoji (NALAZ #37): evaluacijski podaci (attempts, BKT povijest, XP)
# nastaju jednokratno tijekom sesije sa studentima i NENADOKNADIVI su — žive
# samo u docker volumenu `pg_main_data`. Jedan `docker compose down -v` ili
# kvar diska briše cijelu evaluaciju diplomskog rada.
#
# 🔴 Backup koji nije testiran NIJE backup. Ova skripta zato nakon dumpa
# restora u PRIVREMENU bazu i usporedi brojke redaka s izvorom. Ako se ne
# poklapaju, izlazi s ne-nul kodom i dump se NE smije smatrati valjanim.
#
# Pokreni:
#     make backup                       # ili: ./scripts/backup_eval_data.sh
#     ./scripts/backup_eval_data.sh --no-verify   # samo dump (NE preporuča se)
#
# Izlaz: backups/tutor_main_YYYYMMDD_HHMMSS.sql.gz  (ignoriran u gitu)
#
# 🔴 NAKON SVAKE EVAL SESIJE dump kopirati na DRUGI MEDIJ (cloud/vanjski disk).
#    Laptop je jedna točka kvara — backup na istom disku ne štiti od kvara diska.

set -euo pipefail

# --- konfiguracija (izvedena iz docker-compose.yml) ---------------------------
PG_SERVICE="postgres-main"
PG_USER="tutor"
PG_DB="tutor_main"
VERIFY_DB="tutor_main_restore_check"

# Tablice čije brojke redaka moraju preživjeti restore (jezgra evaluacije).
VERIFY_TABLES=(users attempts skill_mastery skill_mastery_history xp_log user_badges streaks tasks agent_messages_log)

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${REPO_ROOT}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUT_FILE="${BACKUP_DIR}/${PG_DB}_${TIMESTAMP}.sql.gz"

DO_VERIFY=1
[[ "${1:-}" == "--no-verify" ]] && DO_VERIFY=0

# --- pomoćne funkcije --------------------------------------------------------
log() { printf '%s\n' "$*"; }
fail() { printf '❌ %s\n' "$*" >&2; exit 1; }

# psql u kontejneru, tab-separated bez zaglavlja
pg() { docker compose exec -T "$PG_SERVICE" psql -U "$PG_USER" -v ON_ERROR_STOP=1 "$@"; }

# Brojke redaka za VERIFY_TABLES iz zadane baze, format "tablica<TAB>broj".
row_counts() {
  local db="$1" sql=""
  for t in "${VERIFY_TABLES[@]}"; do
    sql+="SELECT '${t}' AS t, count(*) AS n FROM ${t} UNION ALL "
  done
  sql="${sql%UNION ALL } ORDER BY t"
  pg -d "$db" -tAF $'\t' -c "$sql"
}

cleanup_verify_db() {
  # terminate + drop; tiho (baza možda ne postoji)
  pg -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${VERIFY_DB}'" \
    >/dev/null 2>&1 || true
  pg -d postgres -c "DROP DATABASE IF EXISTS ${VERIFY_DB}" >/dev/null 2>&1 || true
}

# --- 0. preduvjeti -----------------------------------------------------------
cd "$REPO_ROOT"

docker compose ps --status running --services 2>/dev/null | grep -qx "$PG_SERVICE" \
  || fail "Servis '${PG_SERVICE}' ne vrti. Pokreni: make infra-up"

mkdir -p "$BACKUP_DIR"

log "═══════════════════════════════════════════════════════════"
log " BACKUP ${PG_DB} → ${OUT_FILE#"$REPO_ROOT"/}"
log "═══════════════════════════════════════════════════════════"

# --- 1. stanje izvora PRIJE dumpa -------------------------------------------
log ""
log "▸ Izvorno stanje (${PG_DB}):"
SOURCE_COUNTS="$(row_counts "$PG_DB")"
printf '%s\n' "$SOURCE_COUNTS" | awk -F'\t' '{printf "    %-24s %s\n", $1, $2}'

# --- 2. dump -----------------------------------------------------------------
# Bez --clean/--create: restore ide u SVJEŽU praznu bazu (vidi korak 4), pa
# dump ne smije sadržavati DROP naredbe koje bi mogle pogoditi živu bazu ako
# ga netko greškom pusti u `tutor_main`.
log ""
log "▸ pg_dump u tijeku..."
docker compose exec -T "$PG_SERVICE" pg_dump -U "$PG_USER" -d "$PG_DB" \
  | gzip -9 > "$OUT_FILE"

[[ -s "$OUT_FILE" ]] || fail "Dump je prazan: ${OUT_FILE}"

SIZE_BYTES="$(stat -c %s "$OUT_FILE")"
SIZE_HUMAN="$(du -h "$OUT_FILE" | cut -f1)"
log "  ✓ zapisano: ${SIZE_HUMAN} (${SIZE_BYTES} B)"

# Zdravorazumski donji prag: ispod ~1 kB dump ne može sadržavati ni shemu.
(( SIZE_BYTES > 1024 )) || fail "Dump je sumnjivo malen (${SIZE_BYTES} B) — vjerojatno neuspio."

# gzip integritet (otkriva skraćen zapis pri punom disku)
gzip -t "$OUT_FILE" || fail "gzip integritet pao — dump je oštećen."
log "  ✓ gzip integritet OK"

if (( DO_VERIFY == 0 )); then
  log ""
  log "⚠️  VERIFIKACIJA PRESKOČENA (--no-verify) — ovaj dump NIJE potvrđen kao restore-abilan."
  log "📁 ${OUT_FILE}"
  exit 0
fi

# --- 3. restore u privremenu bazu -------------------------------------------
log ""
log "▸ Verifikacija restore-a (privremena baza '${VERIFY_DB}')..."
trap cleanup_verify_db EXIT
cleanup_verify_db
pg -d postgres -c "CREATE DATABASE ${VERIFY_DB}" >/dev/null
log "  ✓ privremena baza stvorena"

# ON_ERROR_STOP=1 → ne-nul exit ako ijedna naredba iz dumpa padne.
if ! gunzip -c "$OUT_FILE" \
  | docker compose exec -T "$PG_SERVICE" psql -U "$PG_USER" -d "$VERIFY_DB" \
      -v ON_ERROR_STOP=1 -q >/dev/null; then
  fail "RESTORE PAO — dump se ne može vratiti. NE oslanjaj se na ovaj backup."
fi
log "  ✓ restore prošao bez greške"

# --- 4. usporedba brojki -----------------------------------------------------
RESTORED_COUNTS="$(row_counts "$VERIFY_DB")"

log ""
log "  ┌────────────────────────┬──────────┬──────────┬────────┐"
log "  │ tablica                │   izvor  │  restore │ status │"
log "  ├────────────────────────┼──────────┼──────────┼────────┤"

MISMATCH=0
while IFS=$'\t' read -r tbl src_n; do
  res_n="$(printf '%s\n' "$RESTORED_COUNTS" | awk -F'\t' -v t="$tbl" '$1==t {print $2}')"
  if [[ "$src_n" == "$res_n" ]]; then
    status="  ✓   "
  else
    status="  ✗   "
    MISMATCH=1
  fi
  printf '  │ %-22s │ %8s │ %8s │%s│\n' "$tbl" "$src_n" "${res_n:-—}" "$status"
done <<< "$SOURCE_COUNTS"

log "  └────────────────────────┴──────────┴──────────┴────────┘"

if (( MISMATCH )); then
  fail "BROJKE SE NE POKLAPAJU — backup NIJE valjan. Ne nastavljaj s evalom."
fi

# Sadržajna provjera: same brojke ne dokazuju da su podaci isti. Uspoređujemo
# i agregat po attemptima (najvažnija tablica evaluacije).
SRC_SUM="$(pg -d "$PG_DB" -tAc "SELECT coalesce(sum(xp_awarded),0)||'/'||coalesce(sum(case when is_correct then 1 else 0 end),0) FROM attempts")"
RES_SUM="$(pg -d "$VERIFY_DB" -tAc "SELECT coalesce(sum(xp_awarded),0)||'/'||coalesce(sum(case when is_correct then 1 else 0 end),0) FROM attempts")"
[[ "$SRC_SUM" == "$RES_SUM" ]] \
  || fail "Agregat attempta se razlikuje (izvor ${SRC_SUM} vs restore ${RES_SUM}) — backup NIJE valjan."
log ""
log "  ✓ agregat attempta (Σxp/Σtočnih) identičan: ${SRC_SUM}"

cleanup_verify_db
trap - EXIT
log "  ✓ privremena baza obrisana"

# --- 5. sažetak --------------------------------------------------------------
log ""
log "═══════════════════════════════════════════════════════════"
log " ✅ BACKUP VALJAN I RESTORE-ABILAN"
log "═══════════════════════════════════════════════════════════"
log " 📁 ${OUT_FILE}"
log " 📦 ${SIZE_HUMAN}"
log ""
log " 🔴 SLJEDEĆI KORAK — kopiraj na DRUGI MEDIJ:"
log "      cp '${OUT_FILE}' /mnt/c/Users/<ti>/OneDrive/diplomski-backups/"
log "    Backup na istom disku ne štiti od kvara diska."
log ""
ls -1t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -5 | sed 's|^|    |' \
  | { echo " Zadnji backupi:"; cat; }
