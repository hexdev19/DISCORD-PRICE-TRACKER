from __future__ import annotations

import discord
from discord import app_commands

from app.db.session import SessionFactory
from app.repositories.server_repo import ServerRepository


def is_admin(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    return interaction.user.guild_permissions.manage_guild


async def has_tracker_role(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.manage_guild:
        return True
    async with SessionFactory() as session:
        server = await ServerRepository(session).get_by_guild_id(interaction.guild.id)
    if server is None or server.tracker_role_id is None:
        return False
    return any(role.id == server.tracker_role_id for role in interaction.user.roles)


def require_admin() -> "app_commands.Check":
    async def predicate(interaction: discord.Interaction) -> bool:
        return is_admin(interaction)

    return app_commands.check(predicate)


def require_tracker_role() -> "app_commands.Check":
    async def predicate(interaction: discord.Interaction) -> bool:
        return await has_tracker_role(interaction)

    return app_commands.check(predicate)
