import discord
import logging
from discord.ext import commands
from discord import app_commands

from repos import GuildRepository

logger = logging.getLogger(__name__)

# Repository will be injected at startup
guild_repository: GuildRepository | None = None


def _check_repository():
    """Ensure repository is initialized."""
    if guild_repository is None:
        raise RuntimeError("Repository not initialized. Check bot startup.")


@app_commands.command(name="whisper", description="Send an anonymous message to the configured channel.")
@app_commands.describe(message="The message to send anonymously.")
async def whisper(interaction: discord.Interaction, message: str):
    """Send an anonymous message to the configured channel."""
    try:
        _check_repository()
        channel_id = await guild_repository.get_anonymous_channel(interaction.guild_id)
        member = await interaction.guild.fetch_member(interaction.user.id)
        player = await guild_repository.get_player(interaction.guild_id, member.id)
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                if player:
                    message = f"{player.emoji}: {message}"
                    await channel.send(message)
                    logger.info(f"Sent anonymous message in guild {interaction.guild_id} to channel {channel_id} from {member.display_name} with {player.emoji}")
                    await interaction.response.send_message("Your anonymous message has been sent!", ephemeral=True)
                else:
                    await interaction.response.send_message("You need to set up your player profile with an emoji before sending anonymous messages. Please have an admin set it up.", ephemeral=True)
            else:
                await interaction.response.send_message("The configured anonymous channel no longer exists.", ephemeral=True)
        else:
            await interaction.response.send_message("No anonymous channel has been set yet. Please ask an admin to set one up.", ephemeral=True)
    except Exception as e:
        logger.error(f"Error sending anonymous message: {e}")
        await interaction.response.send_message("Failed to send anonymous message. Please try again.", ephemeral=True)


def setup(bot: commands.Bot, repository: GuildRepository):
    """Register commands and inject repository."""
    global guild_repository
    guild_repository = repository

    logger.info("Setting up whisper commands.")
    bot.tree.add_command(whisper)
    logger.info("Whisper commands registered.")