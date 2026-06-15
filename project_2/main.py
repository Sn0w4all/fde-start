"""Entrypoint: wire dependencies and run aiogram long-polling."""
from __future__ import annotations

import asyncio

import structlog
from aiogram import Bot, Dispatcher

import logging_setup
import storage
from bot import handlers
from bot.handlers import Deps, router
from bot.queue import TaskQueue
from config import settings
from core.render import Renderer
from storage import db

log = structlog.get_logger(__name__)


async def main() -> None:
    logging_setup.configure()
    db.configure(settings.db_path)
    await storage.init_db()

    bot = Bot(token=settings.telegram_bot_token)
    renderer = Renderer()
    await renderer.start()
    queue = TaskQueue(
        max_concurrent=settings.max_concurrent_tasks,
        task_timeout_sec=settings.task_timeout_sec,
    )
    handlers.init(Deps(bot=bot, renderer=renderer, queue=queue))

    dp = Dispatcher()
    dp.include_router(router)

    log.info("starting", model=settings.model, admins=settings.admin_ids)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await queue.drain()
        await renderer.stop()
        await bot.session.close()
        log.info("stopped")


if __name__ == "__main__":
    asyncio.run(main())
