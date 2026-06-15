#!/usr/bin/env bash
# Roll back to the previous image (html-bot-bot:prev) tagged by the last deploy.
# Optionally restore code from the latest snapshot too (--code).
set -euo pipefail
cd "$(dirname "$0")/.."

ts() { date -u +%FT%TZ; }

if ! docker image inspect html-bot-bot:prev >/dev/null 2>&1; then
  echo "no html-bot-bot:prev image to roll back to" >&2
  exit 1
fi

if [ "${1:-}" = "--code" ]; then
  SNAP="$(ls -1t ops/backups/pre_*.tgz 2>/dev/null | head -1 || true)"
  if [ -n "$SNAP" ]; then
    echo "restoring code from $SNAP"
    tar xzf "$SNAP"
  fi
fi

docker compose down
docker image tag html-bot-bot:prev html-bot-bot:latest
docker compose up -d
sleep 5
docker compose logs --tail 15 bot
echo "$(ts) | rolled back" >> ops/heal.log
bash ops/notify.sh "↩️ HTML-bot: rolled back to previous version." || true
