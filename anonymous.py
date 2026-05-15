import discord
import logging
from discord import app_commands
from discord.ext import commands
from typing import Optional

from repos import GuildRepository

logger = logging.getLogger(__name__)

# Repository will be injected at startup
guild_repository: GuildRepository | None = None


def _check_repository():
    """Ensure repository is initialized."""
    if guild_repository is None:
        raise RuntimeError("Repository not initialized. Check bot startup.")


@app_commands.command(name="set_anonymous_channel", description="Set the channel for anonymous messages.")
@app_commands.describe(channel="Optional text channel to use for anonymous messages. If not provided, the current channel will be used.")
@app_commands.checks.has_permissions(manage_guild=True)
async def set_anonymous_channel(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
    """Set the channel for anonymous messages."""
    try:
        _check_repository()
        target_channel = channel or interaction.channel
        await guild_repository.set_anonymous_channel(interaction.guild_id, target_channel.id)
        logger.info(f"Set anonymous channel for guild {interaction.guild_id} to {target_channel.id}")
        await interaction.response.send_message(f"Anonymous messages will now be sent to {target_channel.mention}.")
    except Exception as e:
        logger.error(f"Error setting anonymous channel: {e}")
        await interaction.response.send_message("Failed to set anonymous channel. Please try again.")


@app_commands.command(name="get_anonymous_channel", description="Get the current channel for anonymous messages.")
@app_commands.checks.has_permissions(manage_guild=True)
async def get_anonymous_channel(interaction: discord.Interaction):
    """Get the current channel for anonymous messages."""
    try:
        _check_repository()
        channel_id = await guild_repository.get_anonymous_channel(interaction.guild_id)
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                await interaction.response.send_message(f"Anonymous messages are currently sent to {channel.mention}.")
            else:
                await interaction.response.send_message("The configured anonymous channel no longer exists.")
        else:
            await interaction.response.send_message("No anonymous channel has been set yet.")
    except Exception as e:
        logger.error(f"Error getting anonymous channel: {e}")
        await interaction.response.send_message("Failed to retrieve anonymous channel. Please try again.")


@app_commands.command(name="clear_anonymous_channel", description="Clear the anonymous channel setting.")
@app_commands.checks.has_permissions(manage_guild=True)
async def clear_anonymous_channel(interaction: discord.Interaction):
    """Clear the anonymous channel setting."""
    try:
        _check_repository()
        await guild_repository.clear_anonymous_channel(interaction.guild_id)
        logger.info(f"Cleared anonymous channel for guild {interaction.guild_id}")
        await interaction.response.send_message("Anonymous channel setting has been cleared")
    except Exception as e:
        logger.error(f"Error clearing anonymous channel: {e}")
        await interaction.response.send_message("Failed to clear anonymous channel. Please try again.")


@app_commands.command(name="add_player", description="Add a player to the guild's player list.")
@app_commands.describe(member="The member to add.")
@app_commands.describe(emoji="The emoji to associate with the player.")
@app_commands.checks.has_permissions(manage_guild=True)
async def add_player(interaction: discord.Interaction, member: discord.Member, emoji: str):
    """Add a player to the guild's player list."""
    try:
        _check_repository()
        await guild_repository.add_player(
            interaction.guild_id,
            member.id,
            member.display_name,
            emoji
        )
        logger.info(f"Added player {member.display_name} with emoji '{emoji}' to guild {interaction.guild_id}")
        await interaction.response.send_message(f"Added {member.mention} as a player with emoji '{emoji}'.")
    except Exception as e:
        logger.error(f"Error adding player: {e}")
        await interaction.response.send_message("Failed to add player. Please try again.")


@app_commands.command(name="show_players", description="Get the list of players in the guild with their associated emojis.")
@app_commands.checks.has_permissions(manage_guild=True)
async def show_players(interaction: discord.Interaction):
    """Get the list of players in the guild with their associated emojis."""
    try:
        _check_repository()
        players = await guild_repository.list_players(interaction.guild_id)
        if not players:
            await interaction.response.send_message("No players have been added yet.")
            return

        player_list = "\n".join(f"{player.emoji} - {player.discord_display_name}" for player in players)
        await interaction.response.send_message(f"Current players:\n{player_list}")
    except Exception as e:
        logger.error(f"Error showing players: {e}")
        await interaction.response.send_message("Failed to retrieve players. Please try again.")


@app_commands.command(name="remove_player", description="Remove a player from the guild's player list.")
@app_commands.checks.has_permissions(manage_guild=True)
async def remove_player(interaction: discord.Interaction, member: discord.Member):
    """Remove a player from the guild's player list."""
    try:
        _check_repository()
        removed_player = await guild_repository.remove_player(interaction.guild_id, member.id)
        if removed_player:
            logger.info(f"Removed player {removed_player.discord_display_name} from guild {interaction.guild_id}")
            await interaction.response.send_message(f"Removed {removed_player.discord_display_name} from the player list.")
        else:
            await interaction.response.send_message(f"{member.display_name} is not in the player list.")
    except Exception as e:
        logger.error(f"Error removing player: {e}")
        await interaction.response.send_message("Failed to remove player. Please try again.")

def setup(bot: commands.Bot, repository: GuildRepository):
    """Setup anonymous commands with repository dependency injection."""
    global guild_repository
    guild_repository = repository
    
    logger.info("Setting up anonymous commands...")
    bot.tree.add_command(set_anonymous_channel)
    bot.tree.add_command(get_anonymous_channel)
    bot.tree.add_command(clear_anonymous_channel)
    bot.tree.add_command(add_player)
    bot.tree.add_command(show_players)
    bot.tree.add_command(remove_player)
    logger.info("Anonymous commands setup complete.")