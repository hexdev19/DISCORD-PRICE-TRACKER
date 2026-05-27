from __future__ import annotations

import discord
from discord import app_commands

from app.utils import embed_builder
from app.utils.logger import get_logger

log = get_logger(__name__)


async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.CheckFailure):
        await _reply(interaction, "You don't have permission to use this command.")
        return
    if isinstance(error, app_commands.CommandOnCooldown):
        await _reply(interaction, f"Slow down — try again in {int(error.retry_after)}s.")
        return

    log.exception(
        "command.error",
        command=getattr(interaction.command, "qualified_name", "?"),
        error=type(error).__name__,
    )
    await _reply(interaction, "Something went wrong. The team has been notified.")


async def _reply(interaction: discord.Interaction, message: str) -> None:
    embed = discord.Embed.from_dict(embed_builder.error_embed(message))
    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except (discord.HTTPException, discord.InteractionResponded):
        pass
