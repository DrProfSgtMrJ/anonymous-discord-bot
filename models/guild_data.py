from dataclasses import dataclass, field
from typing import Optional

from .player import Player

@dataclass
class GuildData:
    guild_id: int
    anonymous_channel_id: Optional[int] = None
    players: dict[int, Player] = field(default_factory=dict)

    def add_player(self, player: Player):
        self.players[player.discord_member_id] = player

    def set_anonymous_channel_id(self, channel_id: int):
        self.anonymous_channel_id = channel_id

    def clear_anonymous_channel_id(self):
        self.anonymous_channel_id = None
