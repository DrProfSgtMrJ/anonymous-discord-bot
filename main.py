import os
import logging
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

from anonymous import setup as anonymous_setup
from whisper import setup as whisper_setup
from repos import GuildRepository
from migration import import_legacy_data


load_dotenv()

logger_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "discord_bot")

intents = Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Global MongoDB client and repository
mongo_client: AsyncIOMotorClient | None = None
guild_repository: GuildRepository | None = None


async def main():
    global mongo_client, guild_repository
    
    # Initialize MongoDB connection
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[MONGO_DB]
    guild_repository = GuildRepository(db)
    
    # Ensure indexes are created
    await guild_repository.ensure_indexes()
    logging.info(f"Connected to MongoDB at {MONGO_URI}")
    
    # Run migration for legacy data if it exists
    legacy_data_path = os.getenv("LEGACY_DATA_PATH")
    await import_legacy_data(guild_repository, legacy_data_path)
    
    async with bot:
        anonymous_setup(bot, guild_repository)
        whisper_setup(bot, guild_repository)
        await bot.start(token=DISCORD_TOKEN)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Bot is ready! Synced {len(synced)} global commands.")


@bot.event
async def on_error(event, *args, **kwargs):
    """Handle uncaught errors in event handlers."""
    logging.exception(f"Error in {event}:")


async def on_shutdown():
    """Cleanup on bot shutdown."""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logging.info("Closed MongoDB connection")


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logger_handler],
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())