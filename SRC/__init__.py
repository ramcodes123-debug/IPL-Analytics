"""IPL Analytics source package."""

from .data_loader import load_data
from .player_analytics import (
    get_batting_stats,
    get_bowling_stats,
    get_player_top_performances,
)
from .team_analytics import get_team_stats, get_head_to_head
from .match_analytics import get_match_scorecard

__all__ = [
    "load_data",
    "get_batting_stats",
    "get_bowling_stats",
    "get_player_top_performances",
    "get_team_stats",
    "get_head_to_head",
    "get_match_scorecard",
]