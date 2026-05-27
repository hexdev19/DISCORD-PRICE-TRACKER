from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.base import BaseCog
from app.bot.permissions import require_admin
from app.config.limits import WATCHES_PER_SERVER
from app.db.session import SessionFactory
from app.repositories.server_repo import ServerRepository
from app.repositories.watch_repo import WatchRepository
from app.services.server_service import ServerService
from app.utils import embed_builder


class ConfigCog(BaseCog):
    config = app_commands.Group(
        name="config", description="Configure the price tracker", guild_only=True
    )

    @config.command(name="role", description="Set the tracker role")
    @require_admin()
    async def role(self, interaction: discord.Interaction, role: discord.Role) -> None:
        assert interaction.guild is not None
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            await ServerService(session).update_config(
                server.id, actor_id=str(interaction.user.id), tracker_role_id=role.id
            )
            await session.commit()
        await interaction.response.send_message(
            f"Tracker role set to {role.mention}.", ephemeral=True
        )

    @config.command(name="channel", description="Set the default alert channel")
    @require_admin()
    async def channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ) -> None:
        assert interaction.guild is not None
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            await ServerService(session).update_config(
                server.id,
                actor_id=str(interaction.user.id),
                default_alert_channel_id=channel.id,
            )
            await session.commit()
        await interaction.response.send_message(
            f"Alerts will be sent to {channel.mention}.", ephemeral=True
        )

    @config.command(name="role-mention", description="Set the default mention role")
    @require_admin()
    async def role_mention(
        self, interaction: discord.Interaction, role: discord.Role | None = None
    ) -> None:
        assert interaction.guild is not None
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            await ServerService(session).update_config(
                server.id,
                actor_id=str(interaction.user.id),
                default_alert_role_id=role.id if role else None,
            )
            await session.commit()
        await interaction.response.send_message(
            "Mention role updated." if role else "Mention role cleared.", ephemeral=True
        )

    @config.command(name="region", description="Default region for new watches (ISO 3166-1 alpha-2)")
    @require_admin()
    async def region(self, interaction: discord.Interaction, code: str) -> None:
        assert interaction.guild is not None
        normalized = code.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            await interaction.response.send_message(
                "Region must be a 2-letter country code (e.g. US, GB).", ephemeral=True
            )
            return
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            await ServerService(session).update_config(
                server.id, actor_id=str(interaction.user.id), region_default=normalized
            )
            await session.commit()
        await interaction.response.send_message(
            f"Region set to {normalized}.", ephemeral=True
        )

    @config.command(name="show", description="Show current configuration")
    async def show(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            count = await WatchRepository(session).count_active_for_server(server.id)
        embed = discord.Embed.from_dict(
            embed_builder.config_show(server, count, WATCHES_PER_SERVER[server.plan])
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @config.command(name="reset", description="Wipe server configuration (does not delete watches)")
    @require_admin()
    async def reset(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        async with SessionFactory() as session:
            server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
            assert server is not None
            await ServerService(session).update_config(
                server.id,
                actor_id=str(interaction.user.id),
                tracker_role_id=None,
                default_alert_channel_id=None,
                default_alert_role_id=None,
                region_default=None,
            )
            await session.commit()
        await interaction.response.send_message("Configuration reset.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ConfigCog())
