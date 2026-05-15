import os
import logging
import discord
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands


from anonymous import setup as anonymous_setup


load_dotenv()

logger_handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
intents = Intents.default()

intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


async def main():
    async with bot:
        anonymous_setup(bot)
        await bot.start(token=DISCORD_TOKEN)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Bot is ready! Synced {len(synced)} global commands.")

if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG, handlers=[logger_handler], format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main())