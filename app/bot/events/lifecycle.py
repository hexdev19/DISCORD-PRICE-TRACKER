from __future__ import annotations

import discord
from discord.ext import commands

from app.db.session import SessionFactory
from app.repositories.server_repo import ServerRepository
from app.repositories.watch_repo import WatchRepository
from app.services.server_service import ServerService
from app.utils import embed_builder
from app.utils.logger import get_logger

log = get_logger(__name__)


class LifecycleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        async with SessionFactory() as session:
            await ServerService(session).upsert_from_discord(
                guild_id=guild.id,
                name=guild.name,
                icon_hash=str(guild.icon) if guild.icon else None,
            )
            await session.commit()
        log.info("guild.joined", guild_id=guild.id)
        await _dm_inviter(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        async with SessionFactory() as session:
            await ServerService(session).soft_remove(guild.id)
            await session.commit()
        log.info("guild.removed", guild_id=guild.id)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(role.guild.id)
            if server is None:
                return
            if server.tracker_role_id == role.id:
                server.tracker_role_id = None
            if server.default_alert_role_id == role.id:
                server.default_alert_role_id = None
            watches = await WatchRepository(session).list_for_server(server.id)
            for w in watches:
                if w.alert_role_id == role.id:
                    w.alert_role_id = None
            await session.commit()
        log.info("role.deleted", guild_id=role.guild.id, role_id=role.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(channel.guild.id)
            if server is None:
                return
            if server.default_alert_channel_id == channel.id:
                server.default_alert_channel_id = None
            watches = await WatchRepository(session).list_for_server(server.id)
            for w in watches:
                if w.alert_channel_id == channel.id:
                    w.alert_channel_id = None
            await session.commit()
        log.info("channel.deleted", guild_id=channel.guild.id, channel_id=channel.id)


async def _dm_inviter(guild: discord.Guild) -> None:
    inviter: discord.User | discord.Member | None = guild.owner
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=1):
            inviter = entry.user or inviter
            break
    except (discord.Forbidden, discord.HTTPException):
        pass
    if inviter is None:
        return
    try:
        await inviter.send(embed=discord.Embed.from_dict(embed_builder.setup_hint()))
    except (discord.Forbidden, discord.HTTPException):
        pass
