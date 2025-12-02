"""Tests for color utility functions."""


from utils.colors import TEAM_COLORS, TIRE_COLORS, get_team_color, get_tire_color


def test_tire_colors_defined() -> None:
    """Test that all expected tire compounds have colors."""
    expected_compounds = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]

    for compound in expected_compounds:
        assert compound in TIRE_COLORS
        assert TIRE_COLORS[compound].startswith("#")


def test_team_colors_defined() -> None:
    """Test that major teams have colors defined."""
    expected_teams = [
        "Red Bull Racing",
        "Ferrari",
        "Mercedes",
        "McLaren",
    ]

    for team in expected_teams:
        assert team in TEAM_COLORS
        assert TEAM_COLORS[team].startswith("#")


def test_get_tire_color() -> None:
    """Test tire color getter function."""
    # Test known compound
    color = get_tire_color("SOFT")
    assert color == TIRE_COLORS["SOFT"]

    # Test case insensitive
    color = get_tire_color("soft")
    assert color == TIRE_COLORS["SOFT"]

    # Test unknown compound (should return default)
    color = get_tire_color("UNKNOWN")
    assert color == "#CCCCCC"


def test_get_team_color() -> None:
    """Test team color getter function."""
    # Test known team
    color = get_team_color("Ferrari")
    assert color == TEAM_COLORS["Ferrari"]

    # Test unknown team (should return default)
    color = get_team_color("Unknown Team")
    assert color == "#808080"

