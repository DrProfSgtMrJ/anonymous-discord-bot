import logging
import json
from pathlib import Path
from models.guild_data import GuildData
from models.player import Player

logger = logging.getLogger(__name__)


async def import_legacy_data(repository, legacy_data_path: str | None = None) -> None:
    """
    Import legacy in-memory guild data to MongoDB on startup.
    This is a one-time migration path for existing data.
    
    Args:
        repository: GuildRepository instance
        legacy_data_path: Optional path to JSON file with legacy data
    """
    legacy_store = {}
    
    # Try loading from JSON file if specified
    if legacy_data_path:
        try:
            json_path = Path(legacy_data_path)
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded legacy data from {legacy_data_path}")
                
                # Parse JSON into GuildData objects
                for guild_id_str, guild_data_dict in data.items():
                    guild_id = int(guild_id_str)
                    guild_data = GuildData(
                        guild_id=guild_id,
                        anonymous_channel_id=guild_data_dict.get("anonymous_channel_id")
                    )
                    
                    # Parse players
                    for member_id_str, player_dict in guild_data_dict.get("players", {}).items():
                        player = Player(
                            discord_member_id=int(member_id_str),
                            discord_display_name=player_dict["discord_display_name"],
                            emoji=player_dict["emoji"]
                        )
                        guild_data.players[player.discord_member_id] = player
                    
                    legacy_store[guild_id] = guild_data
        except Exception as e:
            logger.warning(f"Failed to load legacy data from {legacy_data_path}: {e}")
    
    # Import to MongoDB if any legacy data exists
    if legacy_store:
        await repository.import_from_memory(legacy_store)
        logger.info(f"Migration complete: imported {len(legacy_store)} guilds from legacy data")
    else:
        logger.info("No legacy data to import")
