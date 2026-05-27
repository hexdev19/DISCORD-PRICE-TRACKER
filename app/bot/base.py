from __future__ import annotations

import discord
from discord.ext import commands

from app.db.session import SessionFactory
from app.services.server_service import ServerService
from app.services.user_service import UserService


class BaseCog(commands.Cog):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "I only work in servers.", ephemeral=True
            )
            return False
        async with SessionFactory() as session:
            await UserService(session).upsert_from_discord(
                discord_id=interaction.user.id,
                discord_username=str(interaction.user),
                discord_avatar=getattr(interaction.user, "avatar", None)
                and str(interaction.user.avatar),
            )
            await ServerService(session).upsert_from_discord(
                guild_id=interaction.guild.id,
                name=interaction.guild.name,
                icon_hash=getattr(interaction.guild, "icon", None)
                and str(interaction.guild.icon),
            )
            await session.commit()
        return True
