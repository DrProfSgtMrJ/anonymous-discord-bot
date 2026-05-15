import logging
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from models.guild_data import GuildData
from models.player import Player

logger = logging.getLogger(__name__)


class GuildRepository:
    """MongoDB-backed repository for guild data and player lists."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection: AsyncIOMotorCollection = db["guilds"]

    async def get_or_create_guild(self, guild_id: int) -> GuildData:
        """Get existing guild data or create new entry if not found."""
        doc = await self.collection.find_one({"_id": guild_id})
        if doc:
            return self._doc_to_guild_data(doc)
        else:
            # Create new guild document lazily on first access
            guild_data = GuildData(guild_id=guild_id)
            return guild_data

    async def set_anonymous_channel(self, guild_id: int, channel_id: int) -> None:
        """Set the anonymous channel ID for a guild."""
        await self.collection.update_one(
            {"_id": guild_id},
            {"$set": {"anonymous_channel_id": channel_id}},
            upsert=True,
        )
        logger.debug(f"Set anonymous channel {channel_id} for guild {guild_id}")

    async def get_anonymous_channel(self, guild_id: int) -> int | None:
        """Get the anonymous channel ID for a guild."""
        doc = await self.collection.find_one({"_id": guild_id})
        if doc and "anonymous_channel_id" in doc:
            return doc["anonymous_channel_id"]
        return None

    async def clear_anonymous_channel(self, guild_id: int) -> None:
        """Clear the anonymous channel setting for a guild."""
        await self.collection.update_one(
            {"_id": guild_id},
            {"$unset": {"anonymous_channel_id": ""}},
        )
        logger.debug(f"Cleared anonymous channel for guild {guild_id}")

    async def add_player(
        self, guild_id: int, member_id: int, display_name: str, emoji: str
    ) -> None:
        """Add or update a player in the guild's player list."""
        player_doc = {
            "discord_member_id": member_id,
            "discord_display_name": display_name,
            "emoji": emoji,
        }
        await self.collection.update_one(
            {"_id": guild_id},
            {
                "$set": {
                    f"players.{member_id}": player_doc,
                }
            },
            upsert=True,
        )
        logger.debug(
            f"Added/updated player {member_id} ({display_name}) to guild {guild_id}"
        )

    async def get_player(self, guild_id: int, member_id: int) -> Player | None:
        """Get a specific player from the guild's player list."""
        doc = await self.collection.find_one({"_id": guild_id})
        if doc and "players" in doc and str(member_id) in doc["players"]:
            player_doc = doc["players"][str(member_id)]
            return Player(
                discord_member_id=player_doc["discord_member_id"],
                discord_display_name=player_doc["discord_display_name"],
                emoji=player_doc["emoji"],
            )
        return None

    async def remove_player(self, guild_id: int, member_id: int) -> Player | None:
        """Remove a player from the guild's player list and return the removed player."""
        # First get the player doc before removing
        doc = await self.collection.find_one({"_id": guild_id})
        removed_player = None
        if doc and "players" in doc and str(member_id) in doc["players"]:
            player_doc = doc["players"][str(member_id)]
            removed_player = Player(
                discord_member_id=player_doc["discord_member_id"],
                discord_display_name=player_doc["discord_display_name"],
                emoji=player_doc["emoji"],
            )

        # Remove the player
        await self.collection.update_one(
            {"_id": guild_id},
            {"$unset": {f"players.{member_id}": ""}},
        )
        logger.debug(f"Removed player {member_id} from guild {guild_id}")
        return removed_player

    async def list_players(self, guild_id: int) -> list[Player]:
        """Get all players for a guild."""
        doc = await self.collection.find_one({"_id": guild_id})
        if not doc or "players" not in doc or not doc["players"]:
            return []

        players = []
        for member_id, player_doc in doc["players"].items():
            # Skip deleted players marked with $unset
            if player_doc is None:
                continue
            players.append(
                Player(
                    discord_member_id=player_doc["discord_member_id"],
                    discord_display_name=player_doc["discord_display_name"],
                    emoji=player_doc["emoji"],
                )
            )
        return players

    async def get_guild_data(self, guild_id: int) -> GuildData:
        """Get full guild data (channel setting + players list)."""
        doc = await self.collection.find_one({"_id": guild_id})
        if doc:
            return self._doc_to_guild_data(doc)
        else:
            # Return empty guild data if not found (will be persisted on first write)
            return GuildData(guild_id=guild_id)

    def _doc_to_guild_data(self, doc: dict) -> GuildData:
        """Convert MongoDB document to GuildData model."""
        guild_data = GuildData(
            guild_id=doc["_id"],
            anonymous_channel_id=doc.get("anonymous_channel_id"),
        )

        # Deserialize players
        if "players" in doc and doc["players"]:
            for member_id, player_doc in doc["players"].items():
                if player_doc is not None:  # Skip deleted entries
                    player = Player(
                        discord_member_id=player_doc["discord_member_id"],
                        discord_display_name=player_doc["discord_display_name"],
                        emoji=player_doc["emoji"],
                    )
                    guild_data.players[player.discord_member_id] = player

        return guild_data

    async def import_from_memory(self, memory_store: dict[int, GuildData]) -> None:
        """Import existing in-memory guild data into MongoDB (idempotent)."""
        if not memory_store:
            logger.info("No in-memory guild data to import.")
            return

        for guild_id, guild_data in memory_store.items():
            # Check if guild already exists in DB to avoid overwriting
            existing = await self.collection.find_one({"_id": guild_id})
            if existing:
                logger.debug(
                    f"Guild {guild_id} already exists in DB, skipping import."
                )
                continue

            # Build document from guild_data
            doc = {
                "_id": guild_id,
                "anonymous_channel_id": guild_data.anonymous_channel_id,
                "players": {},
            }

            # Add players if any
            for member_id, player in guild_data.players.items():
                doc["players"][member_id] = {
                    "discord_member_id": player.discord_member_id,
                    "discord_display_name": player.discord_display_name,
                    "emoji": player.emoji,
                }

            # Insert into DB
            await self.collection.insert_one(doc)
            logger.info(f"Imported guild {guild_id} with {len(guild_data.players)} players")

    async def ensure_indexes(self) -> None:
        """Create database indexes for efficient queries."""
        # Note: _id field already has a unique index by default in MongoDB
        # No additional indexes needed at this time
        logger.info("MongoDB indexes verified for guild collection")
