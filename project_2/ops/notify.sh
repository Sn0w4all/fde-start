#!/usr/bin/env bash
# Send a Telegram message to the first ADMIN id using the bot token.
# No-op if ADMIN_IDS is unset/placeholder.
set -euo pipefail
cd "$(dirname "$0")/.."

TOKEN=$(grep -E '^TELEGRAM_BOT_TOKEN=' .env | cut -d= -f2- || true)
ADMIN=$(grep -E '^ADMIN_IDS=' .env | cut -d= -f2- | tr ',' ' ' | awk '{print $1}' || true)

[ -z "${TOKEN:-}" ] && exit 0
[ -z "${ADMIN:-}" ] && exit 0

curl -s "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${ADMIN}" \
  --data-urlencode "text=${1:-(no message)}" >/dev/null || true
