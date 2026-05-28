from __future__ import annotations

import asyncio

import discord
from celery import Celery
from discord.ext import commands

from app.bot.cogs import COG_MODULES
from app.bot.events.errors import on_app_command_error
from app.bot.events.lifecycle import LifecycleCog
from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.sentry import init_sentry
from app.observability.tracing import init_tracing
from app.services import queue as task_queue
from app.utils.logger import get_logger

log = get_logger(__name__)


class PriceTrackerBot(commands.Bot):
    async def setup_hook(self) -> None:
        await self.add_cog(LifecycleCog(self))
        for module in COG_MODULES:
            await self.load_extension(module)
        synced = await self.tree.sync()
        log.info("bot.ready", cogs=list(self.cogs), commands_synced=len(synced))


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.guilds = True
    bot = PriceTrackerBot(command_prefix="!unused", intents=intents)
    bot.tree.on_error = on_app_command_error  # type: ignore[assignment]
    return bot


def _configure_queue() -> None:
    settings = get_settings()
    celery_client = Celery(broker=settings.redis_url, backend=settings.redis_url)
    task_queue.configure(task_queue.CeleryTaskQueue(celery_client))


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_sentry("bot")
    init_tracing("bot")
    _configure_queue()

    bot = build_bot()
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
