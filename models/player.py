from dataclasses import dataclass


@dataclass
class Player:
    discord_member_id: int
    discord_display_name: str
    emoji: str
    
