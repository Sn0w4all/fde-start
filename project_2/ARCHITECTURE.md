# Architecture — HTML Bot

Stateless Telegram agent that turns **text and/or an image into one self-contained
HTML document** (+ a PNG preview). Each request is processed independently — no
conversation context is persisted. The only durable state is the fact that a user
is authorized.

---

## 1. High-level picture

```
                        Telegram
                           │  long-polling (aiogram 3)
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│  main.py  — wires deps, owns lifecycle (db, renderer, queue, polling)  │
└───────────────┬───────────────────────────────┬──────────────────────┘
                │                                 │
        bot/ (I/O edge)                    core/ (generation)
                │                                 │
   ┌────────────┴───────────┐        ┌────────────┴───────────────────────┐
   │ handlers.py            │        │ pipeline.py  (orchestration)        │
   │  • commands /start…    │        │   ├─ run_text2html                  │
   │  • auth gate           │        │   └─ run_img2html                   │
   │  • dispatch + reply    │        │ llm.py       (Claude API + cache)   │
   │ routing.py (pure)      │        │ render.py    (Playwright + validate)│
   │ queue.py (concurrency, │        │ compare.py   (tile diff, Pillow)    │
   │   timeout, on_error)   │        │ html_utils.py(extract/validate doc) │
   └────────────┬───────────┘        │ retry.py     (exponential backoff)  │
                │                     └─────────────────────────────────────┘
        storage/db.py                            │
   users(tg_id PK, authorized_at)        Anthropic API (Sonnet, vision)
        aiosqlite                        Chromium headless (render→PNG)
```

**Two layers, one rule:** `bot/` owns everything Telegram-shaped (auth, routing,
queueing, message I/O). `core/` is pure generation logic — it knows nothing about
Telegram and is unit-testable with mocks. `main.py` injects `core` deps into `bot`
via a `Deps` dataclass.

---

## 2. Module responsibilities

| Module | Responsibility | Key symbols |
|---|---|---|
| `config.py` | Typed config from `.env` (pydantic-settings). `ADMIN_IDS` parsed from comma/space/JSON. | `Settings`, `settings` |
| `logging_setup.py` | structlog → JSON to stdout. No PII. | `configure()` |
| `main.py` | Entrypoint. Init db → start Renderer → build TaskQueue → inject `Deps` → run polling. Graceful shutdown drains queue, stops renderer. | `main()` |
| `bot/handlers.py` | Command handlers, authorization gate, input dispatch into the queue, artifact delivery. | `on_content`, `_process`, `_send_artifact`, `Deps` |
| `bot/routing.py` | Pure input routing (text / image / both / empty). No side effects → trivially testable. | `route_input`, `Route` |
| `bot/queue.py` | Bounded-concurrency fire-and-forget runner. Per-task timeout; `on_error` callback on timeout/failure. | `TaskQueue` |
| `core/pipeline.py` | Orchestrates the two generation branches and their validation/correction loops. | `run_text2html`, `run_img2html`, `Artifact` |
| `core/llm.py` | All Claude calls. Owns the **cached IMG2HTML conversation**, deterministic output extraction, retries. | `text_to_html`, `start_image_conversation`, `correct_in_conversation`, `regenerate_clean` |
| `core/render.py` | Long-lived headless Chromium. Renders HTML→PNG; `validate()` = artifact guard + render + console-error check. | `Renderer`, `validate`, `RenderError` |
| `core/compare.py` | Splits original & render into an N×N grid, scores per-tile divergence (Pillow). | `compare`, `CompareResult` |
| `core/html_utils.py` | Deterministic slice of `<!DOCTYPE html>…</html>` out of model output; "is this a clean standalone document" check. | `extract_html_document`, `looks_like_html_document` |
| `core/retry.py` | Exponential backoff with jitter for transient API errors. | `with_backoff` |
| `storage/db.py` | SQLite auth store. Only `users(tg_id PK, authorized_at)`. | `is_authorized`, `authorize`, `revoke`, `stats` |
| `ops/` | Self-heal loop (monitor → auto-fix → gated deploy). See §7. | `selfheal.sh`, `deploy.sh`, … |

---

## 3. Request lifecycle

```
User message ──▶ handlers.on_content
   │
   ├─ not authorized?  → treat message as codeword → authorize or deny → STOP
   │
   ├─ route_input(has_text, has_image) → TEXT2HTML | IMG2HTML | BOTH | EMPTY
   │
   ├─ reply "Got it, processing…"
   └─ queue.submit(_process, on_error=notify)      ← bounded concurrency + timeout
                     │
                     ▼
        _process (inside the queue)
          • photo? size check → download (temp, in-memory bytes)
          • run branch(es) INDEPENDENTLY (one failing still delivers the other)
          • send each Artifact: .html document + PNG preview
          • report any failed branch / timeout to the user
```

**Authorization gate.** Any message from an unauthorized user is interpreted as the
codeword (`AUTH_CODEWORD`). Match → persisted in SQLite (permanent until admin
`/revoke`). Commands (`/start`, `/help`, admin) are separate handlers.

**Concurrency.** `TaskQueue` = `asyncio.Semaphore(MAX_CONCURRENT_TASKS)` gating
fire-and-forget tasks, each wrapped in `asyncio.wait_for(TASK_TIMEOUT_SEC)`. On
timeout or unexpected failure the `on_error` callback notifies the user.

---

## 4. Generation pipelines

### TEXT2HTML  (`run_text2html`)

```
prompt ──▶ llm.text_to_html ──▶ validate(render)
                ▲                      │ fail (RenderError)
                └──── retry ≤2 with error feedback ◀──┘
        success → Artifact(html, preview_png)
```

### IMG2HTML  (`run_img2html`) — the heavy path

```
image ─▶ llm.start_image_conversation ─▶ html v0, [conversation]
         │                                    (original image cached in history)
         ▼
   ┌── correction loop (≤ IMG_MAX_ITERS) ───────────────────────────────┐
   │ render → compare(original, render, grid, threshold)                │
   │   GATE: stop if  overall < threshold  (already close enough)       │
   │              OR  no problem tiles                                   │
   │              OR  divergence stopped falling                        │
   │   else: correct_in_conversation(render + problem zones)            │
   │         (HTML never re-pasted; cached prefix re-read at ~0.1×)     │
   └────────────────────────────────────────────────────────────────────┘
         ▼
   final validation loop (≤ IMG_MAX_ITERS):
     validate(html)  → ok → Artifact
                     → fail → regenerate_clean (HTML-only) → re-check
```

**Diagnostics (`compare.py`).** Both images are split into `IMG_TILE_GRID²` tiles;
mean per-tile pixel divergence (0..1) is scored; tiles above `IMG_DIFF_THRESHOLD`
become "problem zones".

---

## 5. Cross-cutting design decisions

**Token efficiency (Claude = Sonnet 4.6, $3/$15 per 1M).**
- *Cached conversation:* IMG2HTML correction is one growing conversation with a
  single `cache_control` breakpoint on the latest user turn. The original image and
  each prior HTML stay in history → later iterations re-read them at ~0.1× instead
  of resending at full price.
- *No HTML re-paste:* the current HTML lives in history as the assistant turn, so
  correction turns carry only the new render + problem-zone labels.
- *Cheap gate:* a correction (a paid call) is skipped entirely when the overall
  divergence is already below threshold.

**Output integrity.**
- *Deterministic artifact stripping:* every model reply is sliced to
  `<!DOCTYPE html>…</html>` (`html_utils.extract_html_document`) — drops fences and
  any commentary/preamble for **0 tokens**, far more reliable than re-prompting.
- *Artifact guard + final-validation loop:* `validate()` rejects non-standalone
  output before rendering; IMG2HTML regenerates HTML-only (cached, cheap) up to
  `IMG_MAX_ITERS` if validation fails.

**Reliability / UX.**
- Branches run independently — one failing still delivers the other and names what
  failed.
- Timeout / unexpected failure → explicit user notice (never silent).
- Tall preview PNG exceeding Telegram's photo limits → sent as a file instead.
- Transient API errors → `with_backoff` (the SDK also retries).

**Safety.**
- Image size checked against `MAX_IMAGE_MB`.
- Inputs / intermediate files in ephemeral temp dirs, removed after reply.
- structured JSON logs, no message content / PII persisted.
- Stateless: only `users(tg_id, authorized_at)`.

---

## 6. Configuration (`.env`)

| Var | Meaning | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` / `ANTHROPIC_API_KEY` / `AUTH_CODEWORD` | secrets | — (required) |
| `ADMIN_IDS` | admin tg ids (comma/space/JSON) | `[]` |
| `MODEL` | Claude model | `claude-sonnet-4-6` |
| `MAX_IMAGE_MB` | reject larger images | 10 |
| `TASK_TIMEOUT_SEC` | per-task timeout | 600 |
| `MAX_CONCURRENT_TASKS` | queue parallelism | 3 |
| `IMG_TILE_GRID` | diagnostic grid N×N | 3 |
| `IMG_DIFF_THRESHOLD` | per-tile divergence threshold + "close enough" gate | 0.15 |
| `IMG_MAX_ITERS` | max correction / final-validation iterations | 3 |
| `DB_PATH` | SQLite path (compose → `/app/data/auth.db`) | `data/auth.db` |

---

## 7. Deployment & self-heal

**Runtime.** Dockerfile based on `mcr.microsoft.com/playwright/python` (Chromium +
deps preinstalled), deps via `uv`. `docker-compose.yml`: one `bot` service,
`restart: unless-stopped`, named volume `bot-data` for SQLite, json-file log
rotation (10m × 5), `shm_size: 512m` for Chromium.

**Host.** KZ VPS `/opt/html-bot`, shipped via rsync; `ops/deploy.sh` tags a rollback
image and rebuilds.

**Self-heal loop (`ops/`, cron).** `selfheal.sh` (daily/30-min cadence) collects
error lines from `docker compose logs`; on a real code defect it runs Claude Code
headless to fix + test (≤5 cycles), then **gates** — sets `PENDING_DEPLOY` and sends
a Telegram notice; a human runs `ops/deploy.sh` to ship. `rollback.sh` reverts.
Kill switch: `touch ops/DISABLED`.

---

## 8. Testing

Unit tests (no network; Chromium tests auto-skip if absent):
- `test_routing` — input routing.
- `test_auth` — SQLite authorize/revoke/idempotency.
- `test_config` — `ADMIN_IDS` parsing, derived limits.
- `test_html_utils` / `test_html_validator` — artifact extraction + the validation guard.
- `test_llm_cache` — single cache breakpoint, prefix byte-stability, no HTML re-paste.
- `test_compare` — tile-diff scoring.
- `test_pipeline` — TEXT2HTML retries, IMG2HTML gate/convergence, final-validation
  regeneration (mocked LLM + fake renderer).

---

## 9. Known limitations (audit backlog)

- **`max_tokens=8192`** can truncate very large HTML → broken document (needs
  streaming / higher cap). *Highest-priority open item.*
- No queue **backpressure** (unbounded pending tasks under flood).
- **Layered retries** (SDK + `with_backoff`) can stack under sustained rate limits.
- **Pixel-diff** is a noisy proxy for visual match (layout shift → false zones).
- Images sent as **document** (uncompressed) are ignored (only `photo` handled).
- SQLite opens a connection per call (no pooling/WAL).
