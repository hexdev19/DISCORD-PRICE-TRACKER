from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.base import BaseCog
from app.bot.permissions import is_admin, require_tracker_role
from app.bot.responses import format_error
from app.config.limits import WATCHES_PER_SERVER
from app.db.session import SessionFactory
from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.repositories.server_repo import ServerRepository
from app.repositories.watch_repo import WatchRepository
from app.services import queue
from app.services.errors import ServiceError
from app.services.watch_service import WatchService
from app.utils import embed_builder

_PAGE_SIZE = 10


_TRACK_SCRAPE_TIMEOUT_SECONDS = 25.0
_TRACK_SCRAPE_POLL_SECONDS = 1.0


class TrackingCog(BaseCog):
    @app_commands.command(name="track", description="Track a product URL")
    @app_commands.describe(url="The product URL to track")
    @require_tracker_role()
    @app_commands.guild_only()
    async def track(self, interaction: discord.Interaction, url: str) -> None:
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)
        async with SessionFactory() as session:
            try:
                watch = await WatchService(session).add_watch(
                    guild_id=interaction.guild.id,
                    discord_user_id=interaction.user.id,
                    raw_url=url,
                )
                product = await ProductRepository(session).get(watch.product_id)
                assert product is not None
                await session.commit()
            except ServiceError as exc:
                await interaction.followup.send(
                    embed=discord.Embed.from_dict(embed_builder.error_embed(format_error(exc))),
                    ephemeral=True,
                )
                return

       
        queue.enqueue_scrape(product.id, priority="high")

   
        product = await self._await_first_scrape(watch.product_id, since=product.last_scraped_at)

        embed = discord.Embed.from_dict(embed_builder.watch_added(watch, product))
        await interaction.followup.send(embed=embed, ephemeral=True)

    @staticmethod
    async def _await_first_scrape(product_id: uuid.UUID, *, since: datetime | None) -> Product:

        loop = asyncio.get_event_loop()
        deadline = loop.time() + _TRACK_SCRAPE_TIMEOUT_SECONDS
        while True:
            async with SessionFactory() as session:
                product = await ProductRepository(session).get(product_id)
                assert product is not None
            if product.last_scraped_at != since or loop.time() >= deadline:
                return product
            await asyncio.sleep(_TRACK_SCRAPE_POLL_SECONDS)

    @app_commands.command(name="untrack", description="Stop tracking a product")
    @app_commands.describe(id="The watch short ID (from /list)")
    @require_tracker_role()
    @app_commands.guild_only()
    async def untrack(self, interaction: discord.Interaction, id: str) -> None:
        async with SessionFactory() as session:
            watch = await WatchRepository(session).get_by_short_id(id.strip())
            if watch is None:
                await interaction.response.send_message(
                    embed=discord.Embed.from_dict(
                        embed_builder.error_embed("No watch with that ID here.")
                    ),
                    ephemeral=True,
                )
                return
            try:
                await WatchService(session).remove(
                    watch_id=watch.id,
                    discord_user_id=interaction.user.id,
                    is_admin=is_admin(interaction),
                )
                await session.commit()
            except ServiceError as exc:
                await interaction.response.send_message(
                    embed=discord.Embed.from_dict(embed_builder.error_embed(format_error(exc))),
                    ephemeral=True,
                )
                return
        await interaction.response.send_message(f"Stopped tracking `{id}`.", ephemeral=True)

    @app_commands.command(name="list", description="List tracked products in this server")
    @app_commands.describe(page="Page number (10 per page)")
    @require_tracker_role()
    @app_commands.guild_only()
    async def list_watches(self, interaction: discord.Interaction, page: int = 1) -> None:
        assert interaction.guild is not None
        page = max(page, 1)
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            watches = await WatchRepository(session).list_for_server(server.id)
            products = ProductRepository(session)
            rows = []
            for w in watches:
                p = await products.get(w.product_id)
                if p is not None:
                    rows.append((w, p))
            cap = WATCHES_PER_SERVER[server.plan]

        total = len(rows)
        pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
        page = min(page, pages)
        slice_ = rows[(page - 1) * _PAGE_SIZE : page * _PAGE_SIZE]
        embed = discord.Embed.from_dict(
            embed_builder.watch_list(slice_, page=page, pages=pages, total=total, cap=cap)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="info", description="Show detail for one watch")
    @app_commands.describe(id="The watch short ID")
    @require_tracker_role()
    @app_commands.guild_only()
    async def info(self, interaction: discord.Interaction, id: str) -> None:
        from app.repositories.price_repo import PriceSnapshotRepository

        async with SessionFactory() as session:
            watch = await WatchRepository(session).get_by_short_id(id.strip())
            if watch is None:
                await interaction.response.send_message(
                    embed=discord.Embed.from_dict(
                        embed_builder.error_embed("No watch with that ID here.")
                    ),
                    ephemeral=True,
                )
                return
            product = await ProductRepository(session).get(watch.product_id)
            assert product is not None
            history_rows = await PriceSnapshotRepository(session).latest_for_product(
                watch.product_id, limit=30
            )
        history = [row.price for row in reversed(history_rows)]
        embed = discord.Embed.from_dict(embed_builder.watch_info(watch, product, history))
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TrackingCog())
