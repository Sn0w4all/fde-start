# HTML Bot

Stateless Telegram agent that turns **text and/or images into a single self-contained
HTML file** (plus a PNG preview). Each request is processed independently — no
conversation context is stored. Only the fact of a user's authorization persists.

## How it works

| Input | Branch | What happens |
|-------|--------|--------------|
| text only | `TEXT2HTML` | Claude generates one self-contained HTML file; rendered + validated (up to 2 retries on error). |
| photo only | `IMG2HTML` | Vision reconstruction → render → tile-diff diagnostics → global iterative correction → final validation. Correction runs as one **prompt-cached conversation** (original image + prior HTML stay in history → iterations 2+ re-read them at ~0.1× and the HTML is never re-pasted), plus a cheap "already close enough" gate that skips paid corrections. |
| text + photo | both | Runs both branches, returns both results. |

Reply for each result = the `.html` document **+** a PNG preview rendered with Playwright/Chromium.

**Output cleanup & final validation.** Every model reply is deterministically sliced
to just the `<!DOCTYPE html>…</html>` document — any stray commentary/preamble (e.g.
"Looking at the problem zones, I need to fix…") is dropped for free (0 tokens). The
final gate requires a clean standalone document that renders without console errors;
if validation fails (no valid document, or a render error), the bot regenerates on the
cached conversation asking for HTML-only and re-checks, up to `IMG_MAX_ITERS` times,
before sending. Problem-zone resolution is handled by the iterative correction loop.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · aiogram 3 (long-polling) · aiosqlite ·
anthropic (Claude Sonnet, vision) · Playwright (Chromium, headless) · Pillow ·
pydantic-settings · structlog.

```
config.py          # .env config
logging_setup.py   # structlog -> JSON stdout
main.py            # entrypoint, dependency wiring, polling
bot/
  handlers.py      # commands, auth gate, dispatch
  routing.py       # pure input routing (testable)
  queue.py         # bounded-concurrency task queue + per-task timeout
core/
  llm.py           # Claude calls (text2html, image2html, correct)
  render.py        # Playwright render + HTML validation
  compare.py       # Pillow tile-diff diagnostics
  pipeline.py      # TEXT2HTML / IMG2HTML orchestration
  retry.py         # exponential backoff
storage/
  db.py            # SQLite users(tg_id PK, authorized_at)
tests/             # routing, auth, html validator
```

## Local setup (uv)

```bash
cd project_2
uv venv --python 3.12
uv pip install -e ".[dev]"
uv run playwright install chromium      # browser for rendering
cp .env.example .env                     # then fill in real values
uv run python main.py
```

Run tests:

```bash
uv run pytest                            # html-validator tests auto-skip if no Chromium
```

## Configuration (`.env`)

| Var | Meaning |
|-----|---------|
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `ANTHROPIC_API_KEY` | Claude API key |
| `AUTH_CODEWORD` | single shared codeword for all users |
| `ADMIN_IDS` | comma/space separated tg ids (admin commands) |
| `MODEL` | default `claude-sonnet-4-6` |
| `MAX_IMAGE_MB` | reject larger images (default 10) |
| `TASK_TIMEOUT_SEC` | per-task timeout (default 600) |
| `MAX_CONCURRENT_TASKS` | queue parallelism (default 3) |
| `IMG_TILE_GRID` | diagnostic tile grid NxN (default 3) |
| `IMG_DIFF_THRESHOLD` | per-tile divergence threshold (default 0.15) |
| `IMG_MAX_ITERS` | max global correction iterations (default 3) |
| `DB_PATH` | SQLite path (compose sets `/app/data/auth.db`) |

## Commands

- `/start` — greeting; asks for codeword if not authorized.
- `/help` — capabilities (authorized only).
- Unauthorized user: **any** message is treated as the codeword. Match → access granted
  (persisted in SQLite, permanent until revoked). No match → denied.
- Admin: `/grant <tg_id>`, `/revoke <tg_id>`, `/stats`.

## Changing the codeword

Edit `AUTH_CODEWORD` in `.env` and restart. Existing authorizations are **not** affected
(they live in SQLite); the codeword only gates new authorizations. To force a user to
re-authorize, `/revoke <tg_id>` them.

## Deploy (Docker, e.g. on the VPS)

```bash
# on the server
git clone <repo> && cd project_2
cp .env.example .env && nano .env        # fill real secrets
docker compose up -d --build
docker compose logs -f bot
```

The base image is `mcr.microsoft.com/playwright/python` (Chromium + system deps
preinstalled). SQLite lives in the named volume `bot-data` (`/app/data`), so
authorizations survive restarts and rebuilds.

```bash
docker compose pull && docker compose up -d --build   # update
docker compose down                                    # stop
```

## Safety

- Image size checked against `MAX_IMAGE_MB` before download/processing.
- Input images and intermediate render files use ephemeral temp dirs, deleted after reply.
- Structured JSON logging of requests/errors; no PII or message content persisted.
- Exponential backoff on network/API calls.
- Stateless: only `users(tg_id, authorized_at)` is stored.
```
