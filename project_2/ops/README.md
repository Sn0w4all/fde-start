# Self-heal ops

Closed loop on the VPS: **monitor → analyze → auto-fix → test (≤5) → GATE → deploy**.
Deploy is **gated** — the loop never ships on its own; it prepares a tested fix and
notifies you. You approve by running `deploy.sh`.

## Pieces

| File | Role | Who runs it |
|------|------|-------------|
| `collect_errors.sh [window]` | grep error lines from `docker compose logs` → `errors.txt` | cron |
| `selfheal.sh [window]` | orchestrator: collect → claude headless fix+test (≤5) → set `PENDING_DEPLOY` + notify | **cron** |
| `heal_prompt.md` | instructions handed to the headless `claude -p` worker | — |
| `notify.sh "msg"` | Telegram message to first `ADMIN_IDS` | scripts |
| `deploy.sh` | **the gate**: tag rollback image, rebuild, restart, verify | **human** |
| `rollback.sh [--code]` | revert to previous image (and optionally code snapshot) | human |

## Flow

```
cron (daily) ─▶ selfheal.sh
                 ├─ no errors ............................ exit
                 ├─ errors → claude fixes + tests (≤5)
                 │     ├─ green → touch PENDING_DEPLOY, notify you ──▶ you run deploy.sh
                 │     └─ not green → notify you (manual check)
```

State files (in `ops/`):
- `DISABLED` — kill switch. `touch ops/DISABLED` to pause the loop entirely.
- `PENDING_DEPLOY` — a tested fix is waiting for your approval; loop pauses until you deploy.
- `HEAL_OK` — internal handshake from the worker (auto-removed).
- `heal_report.md` — worker's cause+fix summary. `heal.log` — full run log.
- `backups/pre_*.tgz` — code snapshot taken before each auto-edit.

## Install on VPS (one-time)

Node + Claude Code, then cron. See chat / `INSTALL` notes. Cron line:

```
0 4 * * * ANTHROPIC_API_KEY='sk-ant-...' /opt/html-bot/ops/selfheal.sh 25h >> /opt/html-bot/ops/cron.log 2>&1
```
(daily at 04:00 UTC, scanning the last 25h of logs)

## Daily use

```bash
tail -f ops/heal.log              # watch the loop
cat ops/heal_report.md            # see what it wants to change
ops/deploy.sh                     # approve + ship a pending fix
ops/rollback.sh                   # undo last deploy (image only)
ops/rollback.sh --code            # also restore pre-fix code snapshot
touch ops/DISABLED                # pause the loop;  rm ops/DISABLED to resume
```

## Notes / caveats

- **ADMIN_IDS must be real** or Telegram notifications are silently skipped.
- Auto-fixes happen on the **server** copy → it can drift from local `project_2/`.
  After approving a fix, pull it back: `rsync -az --exclude .env --exclude data
  root@5.39.253.253:/opt/html-bot/{bot,core,storage,*.py} project_2/`.
- The worker runs `claude --dangerously-skip-permissions` (unattended, no TTY).
  It is constrained by `heal_prompt.md` (minimal fix, no deploy, no .env) but this is
  the main trust boundary — review `heal_report.md` before every `deploy.sh`.
- Transient/network errors are ignored by design (already retried in code).
