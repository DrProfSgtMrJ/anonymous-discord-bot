import discord
import logging
from discord import app_commands
from discord.ext import commands
from typing import Optional

from models.guild_data import GuildData

logger = logging.getLogger(__name__)

# IN MEMORY GUILD DATA STORAGE
guild_data_store: dict[int, GuildData] = {}

def get_guild_data(guild_id: int) -> GuildData:
    if guild_id not in guild_data_store:
        guild_data_store[guild_id] = GuildData(guild_id=guild_id)
        logger.debug(f"Created new GuildData for guild {guild_id}")
    return guild_data_store[guild_id]



@app_commands.command(name="set_anonymous_channel", description="Set the channel for anonymous messages.")
@app_commands.describe(channel="Optional text channel to use for anonymous messages. If not provided, the current channel will be used.")
async def set_anonymous_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    """Set the channel for anonymous messages."""
    guild_data = get_guild_data(interaction.guild_id)
    target_channel = channel or interaction.channel
    guild_data.set_anonymous_channel_id(target_channel.id)
    logger.info(f"Set anonymous channel for guild {interaction.guild_id} to {target_channel.id}")
    await interaction.response.send_message(f"Anonymous messages will now be sent to {target_channel.mention}.")


def setup(bot: commands.Bot):
    logger.info("Setting up anonymous commands...")
    bot.tree.add_command(set_anonymous_channel)