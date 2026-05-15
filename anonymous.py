import discord
import logging
from discord import app_commands
from discord.ext import commands
from typing import Optional

from models.guild_data import GuildData
from models.player import Player

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
@app_commands.checks.has_permissions(manage_guild=True)
async def set_anonymous_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    """Set the channel for anonymous messages."""
    guild_data = get_guild_data(interaction.guild_id)
    target_channel = channel or interaction.channel
    guild_data.set_anonymous_channel_id(target_channel.id)
    logger.info(f"Set anonymous channel for guild {interaction.guild_id} to {target_channel.id}")
    await interaction.response.send_message(f"Anonymous messages will now be sent to {target_channel.mention}.")


@app_commands.command(name="get_anonymous_channel", description="Get the current channel for anonymous messages.")
@app_commands.checks.has_permissions(manage_guild=True)
async def get_anonymous_channel(interaction: discord.Interaction):
    """Get the current channel for anonymous messages."""
    guild_data = get_guild_data(interaction.guild_id)
    channel_id = guild_data.anonymous_channel_id
    if channel_id:
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await interaction.response.send_message(f"Anonymous messages are currently sent to {channel.mention}.")
        else:
            await interaction.response.send_message("The configured anonymous channel no longer exists.")
    else:
        await interaction.response.send_message("No anonymous channel has been set yet.")


@app_commands.command(name="clear_anonymous_channel", description="Clear the anonymous channel setting.")
@app_commands.checks.has_permissions(manage_guild=True)
async def clear_anonymous_channel(interaction: discord.Interaction):
    """Clear the anonymous channel setting."""
    guild_data = get_guild_data(interaction.guild_id)
    guild_data.clear_anonymous_channel_id()
    logger.info(f"Cleared anonymous channel for guild {interaction.guild_id}")
    await interaction.response.send_message("Anonymous channel setting has been cleared")


@app_commands.command(name="add_player", description="Add a player to the guild's player list.")
@app_commands.describe(member="The member to add.")
@app_commands.describe(emoji="The emoji to associate with the player.")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_player(interaction: discord.Interaction, member: discord.Member, emoji: str):
    """Add a player to the guild's player list."""
    guild_data = get_guild_data(interaction.guild_id)

    player = Player(discord_member_id=member.id, discord_display_name=member.display_name, emoji=emoji)
    guild_data.add_player(player)
    logger.info(f"Added player {member.display_name} with emoji '{emoji}' to guild {interaction.guild_id}")
    await interaction.response.send_message(f"Added {member.mention} as a player with emoji '{emoji}'.")


@app_commands.command(name="show_players", description="Get the list of players in the guild with their associated emojis.")
@app_commands.checks.has_permissions(manage_guild=True)
async def show_players(interaction: discord.Interaction):
    """Get the list of players in the guild with their associated emojis."""
    guild_data = get_guild_data(interaction.guild_id)
    if not guild_data.players:
        await interaction.response.send_message("No players have been added yet.")
        return

    player_list = "\n".join(f"{player.emoji} - {player.discord_display_name}" for player in guild_data.list_players())
    await interaction.response.send_message(f"Current players:\n{player_list}")


@app_commands.command(name="remove_player", description="Remove a player from the guild's player list.")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_player(interaction: discord.Interaction, member: discord.Member):
    """Remove a player from the guild's player list."""
    guild_data = get_guild_data(interaction.guild_id)
    removed_player = guild_data.remove_player(member.id)
    if removed_player:
        logger.info(f"Removed player {removed_player.discord_display_name} from guild {interaction.guild_id}")
        await interaction.response.send_message(f"Removed {removed_player.discord_display_name} from the player list.")
    else:
        await interaction.response.send_message(f"{member.display_name} is not in the player list.")

def setup(bot: commands.Bot):
    logger.info("Setting up anonymous commands...")
    bot.tree.add_command(set_anonymous_channel)
    bot.tree.add_command(get_anonymous_channel)
    bot.tree.add_command(clear_anonymous_channel)
    bot.tree.add_command(add_player)
    bot.tree.add_command(show_players)
    bot.tree.add_command(remove_player)
    logger.info("Anonymous commands setup complete.")