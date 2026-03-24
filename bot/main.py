import asyncio
 
import discord
from discord.ext import commands
 
from config.settings import settings
from utils.logger import get_logger
 
logger = get_logger(__name__)
 
EXTENSIONS: list[str] = [
    "bot.events.handlers",
    "bot.cogs.tracking",
    "bot.cogs.search",
    "bot.cogs.compare",
    "bot.cogs.history",
]
 
 
async def main() -> None:
    intents = discord.Intents.default()
    intents.message_content = True
 
    bot = commands.Bot(command_prefix="!", intents=intents)
 
    logger.info("bot.starting")
 
    async with bot:
        for extension in EXTENSIONS:
            await bot.load_extension(extension)
            logger.info("extension.loaded", extension=extension)
 
        await bot.start(settings.DISCORD_TOKEN)
 
 
asyncio.run(main())