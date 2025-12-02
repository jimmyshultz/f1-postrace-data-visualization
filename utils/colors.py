"""F1 team colors and tire compound colors."""

from functools import lru_cache
from typing import Dict

# Tire Compound Colors (F1 Official)
TIRE_COLORS: Dict[str, str] = {
    "SOFT": "#DA291C",  # Red
    "MEDIUM": "#FFF200",  # Yellow
    "HARD": "#EBEBEB",  # White
    "INTERMEDIATE": "#43B02A",  # Green
    "WET": "#0067AD",  # Blue
}

# Team Colors (2024 season)
TEAM_COLORS: Dict[str, str] = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
}


@lru_cache(maxsize=32)
def get_tire_color(compound: str) -> str:
    """
    Get the official F1 color for a tire compound.

    Args:
        compound: Tire compound name (e.g., 'SOFT', 'MEDIUM', 'HARD')

    Returns:
        Hex color code for the compound
    """
    return TIRE_COLORS.get(compound.upper(), "#CCCCCC")


@lru_cache(maxsize=32)
def get_team_color(team_name: str) -> str:
    """
    Get the team color for a given team.

    Args:
        team_name: Full team name

    Returns:
        Hex color code for the team
    """
    return TEAM_COLORS.get(team_name, "#808080")

