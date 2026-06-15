#!/usr/bin/env bash
# Self-heal orchestrator (runs from cron on the VPS).
# Monitor -> analyze -> auto-fix+test (max 5, inside claude) -> GATE (notify, no deploy).
set -uo pipefail
cd "$(dirname "$0")/.."

LOG="ops/heal.log"
ts() { date -u +%FT%TZ; }
say() { echo "$(ts) | $*" >> "$LOG"; }

# --- kill switch ---
if [ -f ops/DISABLED ]; then say "DISABLED flag present, skipping"; exit 0; fi
# --- don't pile up: a fix is already waiting for human deploy ---
if [ -f ops/PENDING_DEPLOY ]; then say "PENDING_DEPLOY exists, awaiting human deploy, skipping"; exit 0; fi

# claude auth from the bot's key
set -a; ANTHROPIC_API_KEY="$(grep -E '^ANTHROPIC_API_KEY=' .env | cut -d= -f2-)"; set +a
export ANTHROPIC_API_KEY

WINDOW="${1:-35m}"
COUNT="$(bash ops/collect_errors.sh "$WINDOW")"
say "scanned window=$WINDOW error_lines=$COUNT"
if [ "$COUNT" -eq 0 ]; then say "no errors, done"; exit 0; fi

# --- snapshot code for rollback before any auto-edit ---
mkdir -p ops/backups
SNAP="ops/backups/pre_$(date -u +%Y%m%dT%H%M%SZ).tgz"
tar czf "$SNAP" --exclude=ops/backups --exclude=data --exclude=.venv \
  bot core storage config.py main.py logging_setup.py pyproject.toml 2>/dev/null || true
say "snapshot -> $SNAP"

rm -f ops/HEAL_OK ops/heal_report.md

say "invoking claude headless heal worker"
claude -p "$(cat ops/heal_prompt.md)" \
  --allowedTools "Read,Edit,Write,Bash" \
  --dangerously-skip-permissions \
  --max-turns 80 \
  >> "$LOG" 2>&1
say "claude exited rc=$?"

if [ -f ops/HEAL_OK ]; then
  rm -f ops/HEAL_OK
  touch ops/PENDING_DEPLOY
  say "FIX READY (tests green). PENDING_DEPLOY set. Awaiting human deploy."
  REPORT="$(head -c 1500 ops/heal_report.md 2>/dev/null || echo '(no report)')"
  bash ops/notify.sh "$(printf '🛠 HTML-bot: AUTO-FIX READY, tests GREEN.\n\n--- cause + fix ---\n%s\n\n✅ approve+deploy:\n  ssh root@5.39.253.253 '\''cd /opt/html-bot && ops/deploy.sh'\''\n↩️ reject:\n  ssh root@5.39.253.253 '\''cd /opt/html-bot && ops/rollback.sh --code'\''' "$REPORT")"
else
  say "no green fix produced this run"
  ERRSNIP="$(head -c 800 ops/errors.txt 2>/dev/null || true)"
  bash ops/notify.sh "$(printf '⚠️ HTML-bot: errors detected (%s lines), auto-fix did NOT pass tests. Manual check needed.\n\n--- sample ---\n%s' "$COUNT" "$ERRSNIP")"
fi
