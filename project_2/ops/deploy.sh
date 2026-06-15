#!/usr/bin/env bash
# THE GATE: human-approved deploy of the current (possibly auto-fixed) code.
# Tags the previous image for rollback, rebuilds, restarts, verifies.
set -euo pipefail
cd "$(dirname "$0")/.."

ts() { date -u +%FT%TZ; }

# keep a rollback image
docker image tag html-bot-bot:latest html-bot-bot:prev 2>/dev/null || true

echo "$(ts) building + starting…"
docker compose up -d --build

sleep 6
echo "--- recent logs ---"
docker compose logs --tail 20 bot

rm -f ops/PENDING_DEPLOY
echo "$(ts) | deployed" >> ops/heal.log
bash ops/notify.sh "✅ HTML-bot: new version deployed." || true
echo "$(ts) done. Rollback if needed: ops/rollback.sh"
