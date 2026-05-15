from dataclasses import dataclass, field
from typing import Optional

from .player import Player

@dataclass
class GuildData:
    guild_id: int
    anonymous_channel_id: Optional[int] = None
    players: list[Player] = field(default_factory=list)

    def add_player(self, player: Player):
        self.players.append(player)

    def set_anonymous_channel_id(self, channel_id: int):
        self.anonymous_channel_id = channel_id
