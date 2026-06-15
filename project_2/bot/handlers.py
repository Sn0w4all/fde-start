"""aiogram handlers: auth, help, admin commands, generation dispatch."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

import structlog
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

import storage
from bot.queue import TaskQueue
from bot.routing import Route, route_input
from config import settings
from core import pipeline
from core.pipeline import Artifact
from core.render import Renderer

log = structlog.get_logger(__name__)

router = Router()


@dataclass
class Deps:
    bot: Bot
    renderer: Renderer
    queue: TaskQueue


_deps: Deps | None = None


def init(deps: Deps) -> None:
    global _deps
    _deps = deps


def _d() -> Deps:
    assert _deps is not None, "handlers not initialized"
    return _deps


def _is_admin(tg_id: int) -> bool:
    return tg_id in settings.admin_ids


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    uid = message.from_user.id
    if await storage.is_authorized(uid):
        await message.answer(
            "You are authorized. Send text, a photo, or a photo with a caption — "
            "I will generate an HTML page. /help for details."
        )
    else:
        await message.answer(
            "Hi! This bot generates self-contained HTML.\n\n"
            "Please send the codeword to get access."
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not await storage.is_authorized(message.from_user.id):
        await message.answer("Send the codeword first to use the bot.")
        return
    await message.answer(
        "What I do:\n"
        "• text → HTML page describing it\n"
        "• photo → HTML that visually reproduces the image\n"
        "• text + photo → both results\n\n"
        f"Image limit: {settings.max_image_mb} MB.\n"
        "Reply format: an .html document + a PNG preview rendered from it."
    )


# --- admin ---
@router.message(Command("grant"))
async def cmd_grant(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    target = _parse_id_arg(message.text)
    if target is None:
        await message.answer("Usage: /grant <tg_id>")
        return
    await storage.authorize(target)
    await message.answer(f"Granted access to {target}.")


@router.message(Command("revoke"))
async def cmd_revoke(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    target = _parse_id_arg(message.text)
    if target is None:
        await message.answer("Usage: /revoke <tg_id>")
        return
    removed = await storage.revoke(target)
    await message.answer(f"Revoked {target}." if removed else f"{target} was not authorized.")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    s = await storage.stats()
    lines = [f"Authorized users: {s['total']}", "", "Recent:"]
    for tg_id, when in s["recent"]:  # type: ignore[index]
        lines.append(f"  {tg_id} — {when}")
    await message.answer("\n".join(lines))


def _parse_id_arg(text: str | None) -> int | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    try:
        return int(parts[1].strip())
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Content / auth
# --------------------------------------------------------------------------- #
@router.message(F.text | F.photo)
async def on_content(message: Message) -> None:
    uid = message.from_user.id

    # --- authorization gate: any message from an unauthorized user is a codeword ---
    if not await storage.is_authorized(uid):
        candidate = (message.text or message.caption or "").strip()
        if candidate == settings.auth_codeword:
            await storage.authorize(uid)
            await message.answer("Access granted. Send text or a photo to generate HTML.")
        else:
            await message.answer("Wrong codeword. Access denied.")
        return

    has_text = bool((message.text or message.caption or "").strip())
    has_image = bool(message.photo)
    route = route_input(has_text=has_text, has_image=has_image)
    if route is Route.EMPTY:
        await message.answer("Send some text or a photo.")
        return

    await message.answer("Got it, processing…")
    _d().queue.submit(lambda: _process(message, route), name=f"gen-{uid}-{message.message_id}")


async def _process(message: Message, route: Route) -> None:
    """Runs inside the task queue (bounded concurrency + timeout)."""
    d = _d()
    text = (message.text or message.caption or "").strip()

    image_bytes: bytes | None = None
    media_type = "image/jpeg"
    if message.photo:
        photo = message.photo[-1]  # largest size
        if photo.file_size and photo.file_size > settings.max_image_bytes:
            await message.answer(
                f"Image too large ({photo.file_size // (1024 * 1024)} MB). "
                f"Limit is {settings.max_image_mb} MB."
            )
            return
        image_bytes = await _download_photo(d.bot, photo.file_id)
        if len(image_bytes) > settings.max_image_bytes:
            await message.answer(f"Image exceeds {settings.max_image_mb} MB limit.")
            return

    artifacts: list[Artifact] = []
    try:
        if route in (Route.TEXT2HTML, Route.BOTH):
            artifacts.append(await pipeline.run_text2html(d.renderer, text))
        if route in (Route.IMG2HTML, Route.BOTH):
            assert image_bytes is not None
            artifacts.append(await pipeline.run_img2html(d.renderer, image_bytes, media_type))
    except Exception:
        log.exception("generation_failed", route=route.value, user=message.from_user.id)
        if not artifacts:
            await message.answer(
                "Could not generate a valid HTML page for this input. Please try again "
                "or rephrase."
            )

    for art in artifacts:
        await _send_artifact(message, art)


async def _download_photo(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    buf = await bot.download_file(file.file_path)
    return buf.read()


async def _send_artifact(message: Message, art: Artifact) -> None:
    """Send .html document + PNG preview using ephemeral temp files."""
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / f"{art.kind}.html"
        html_path.write_text(art.html, encoding="utf-8")
        await message.answer_document(
            BufferedInputFile(html_path.read_bytes(), filename=html_path.name),
            caption=f"{art.kind}: HTML",
        )
        await message.answer_photo(
            BufferedInputFile(art.png, filename=f"{art.kind}.png"),
            caption=f"{art.kind}: preview",
        )
    # temp dir (and any intermediate files) removed on context exit
