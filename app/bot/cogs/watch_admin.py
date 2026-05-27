from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.base import BaseCog
from app.bot.permissions import is_admin, require_admin, require_tracker_role
from app.bot.responses import format_error
from app.db.session import SessionFactory
from app.repositories.watch_repo import WatchRepository
from app.services.errors import ServiceError
from app.services.watch_service import WatchService
from app.utils import embed_builder


class WatchAdminCog(BaseCog):
    watch = app_commands.Group(
        name="watch", description="Manage a single watch", guild_only=True
    )

    @watch.command(name="threshold", description="Set or clear the price threshold")
    @require_tracker_role()
    async def threshold(
        self, interaction: discord.Interaction, id: str, amount: str
    ) -> None:
        cleared = amount.lower() in ("off", "none", "clear")
        if not cleared:
            try:
                Decimal(amount)
            except InvalidOperation:
                await _reply_error(interaction, "Amount must be a number, or `off`.")
                return
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.update_alert_rules(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                is_admin=is_admin(interaction),
                rules={"threshold": None if cleared else amount},
            ),
            ok=("Threshold cleared." if cleared else f"Threshold set to {amount}."),
        )

    @watch.command(name="alert", description="Enable or disable an alert rule")
    @require_tracker_role()
    async def alert(
        self,
        interaction: discord.Interaction,
        id: str,
        rule: Literal["drop", "restock"],
        mode: Literal["on", "off"],
    ) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.update_alert_rules(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                is_admin=is_admin(interaction),
                rules={rule: mode == "on"},
            ),
            ok=f"{rule} alerts {mode}.",
        )

    @watch.command(name="channel", description="Override the alert channel for one watch")
    @require_admin()
    async def channel(
        self,
        interaction: discord.Interaction,
        id: str,
        channel: discord.TextChannel | None = None,
    ) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.set_channel(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                channel_id=channel.id if channel else None,
            ),
            ok=(f"Alerts for `{id}` will go to {channel.mention}." if channel else "Channel override cleared."),
        )

    @watch.command(name="role", description="Override the mention role for one watch")
    @require_admin()
    async def role(
        self,
        interaction: discord.Interaction,
        id: str,
        role: discord.Role | None = None,
    ) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.set_role_mention(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                role_id=role.id if role else None,
            ),
            ok=(f"Mention role for `{id}` set to {role.mention}." if role else "Mention role cleared."),
        )

    @watch.command(name="pause", description="Pause scraping for one watch")
    @require_tracker_role()
    async def pause(self, interaction: discord.Interaction, id: str) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.pause(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                is_admin=is_admin(interaction),
            ),
            ok=f"Paused `{id}`.",
        )

    @watch.command(name="resume", description="Resume scraping for one watch")
    @require_tracker_role()
    async def resume(self, interaction: discord.Interaction, id: str) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.resume(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                is_admin=is_admin(interaction),
            ),
            ok=f"Resumed `{id}`.",
        )

    @watch.command(name="refresh", description="Request an immediate scrape")
    @require_tracker_role()
    async def refresh(self, interaction: discord.Interaction, id: str) -> None:
        await _call_service(
            interaction,
            id,
            lambda svc, w: svc.request_refresh(
                watch_id=w.id,
                discord_user_id=interaction.user.id,
                is_admin=is_admin(interaction),
            ),
            ok=f"Refresh requested for `{id}`. Results arrive in a few seconds.",
        )


async def _call_service(
    interaction: discord.Interaction,
    short_id: str,
    op,
    *,
    ok: str,
) -> None:
    async with SessionFactory() as session:
        watch = await WatchRepository(session).get_by_short_id(short_id.strip())
        if watch is None:
            await _reply_error(interaction, "No watch with that ID here.")
            return
        try:
            await op(WatchService(session), watch)
            await session.commit()
        except ServiceError as exc:
            await _reply_error(interaction, format_error(exc))
            return
    await interaction.response.send_message(ok, ephemeral=True)


async def _reply_error(interaction: discord.Interaction, message: str) -> None:
    embed = discord.Embed.from_dict(embed_builder.error_embed(message))
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WatchAdminCog())
