#!/usr/bin/env bash
# Pull recent bot errors from docker logs into ops/errors.txt.
# Prints the error line count to stdout.
set -euo pipefail
cd "$(dirname "$0")/.."

SINCE="${1:-30m}"
OUT="ops/errors.txt"

docker compose logs --no-color --since "$SINCE" bot 2>/dev/null \
  | grep -E '"level": ?"error"|task_failed|task_timeout|generation_failed|Traceback|Exception' \
  > "$OUT" || true

wc -l < "$OUT" | tr -d ' '
