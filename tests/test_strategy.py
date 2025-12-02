"""Tests for strategy analysis module."""

from datetime import timedelta

import pandas as pd

from analysis.strategy import calculate_stints, get_pit_stops, get_stints_dataframe


def create_sample_driver_laps() -> pd.DataFrame:
    """Create sample lap data with multiple stints."""
    return pd.DataFrame(
        {
            "Driver": ["VER"] * 15,
            "LapNumber": list(range(1, 16)),
            "LapTime": [timedelta(seconds=88 + i % 3) for i in range(15)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5 + ["HARD"] * 5,
            "TyreLife": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Position": [3, 3, 3, 3, 4, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1],
            "PitInTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 4 + [pd.Timestamp("2024-01-01 12:30:00")]
            + [None] * 5,
            "PitOutTime": [None] * 5 + [pd.Timestamp("2024-01-01 12:00:03")]
            + [None] * 4 + [pd.Timestamp("2024-01-01 12:30:03")]
            + [None] * 4,
        }
    )


def test_calculate_stints() -> None:
    """Test stint calculation."""
    laps = create_sample_driver_laps()
    stints = calculate_stints(laps)

    # Should have 3 stints (SOFT, MEDIUM, HARD)
    assert len(stints) == 3

    # First stint should be SOFT
    assert stints[0].compound == "SOFT"
    assert stints[0].lap_start == 1
    assert stints[0].lap_end == 5
    assert stints[0].laps_completed == 5

    # Second stint should be MEDIUM
    assert stints[1].compound == "MEDIUM"
    assert stints[1].lap_start == 6
    assert stints[1].lap_end == 10

    # Third stint should be HARD
    assert stints[2].compound == "HARD"
    assert stints[2].lap_start == 11
    assert stints[2].lap_end == 15


def test_calculate_stints_tire_age() -> None:
    """Test that tire age is captured correctly."""
    laps = create_sample_driver_laps()
    stints = calculate_stints(laps)

    # Each stint starts with tire age 1
    assert stints[0].tire_age_at_start == 1
    assert stints[1].tire_age_at_start == 1
    assert stints[2].tire_age_at_start == 1


def test_calculate_stints_positions() -> None:
    """Test position tracking in stints."""
    laps = create_sample_driver_laps()
    stints = calculate_stints(laps)

    # First stint: P3 -> P4 (lost 1 position)
    assert stints[0].position_start == 3
    assert stints[0].position_end == 4
    assert stints[0].position_change == 1

    # Third stint: P2 -> P1 (gained 1 position)
    assert stints[2].position_start == 2
    assert stints[2].position_end == 1
    assert stints[2].position_change == -1


def test_get_pit_stops() -> None:
    """Test pit stop extraction."""
    laps = create_sample_driver_laps()
    pit_stops = get_pit_stops(laps)

    # Should have 2 pit stops
    assert len(pit_stops) == 2

    # First pit stop at lap 5
    assert pit_stops.iloc[0]["LapNumber"] == 5
    assert pit_stops.iloc[0]["Duration"] == 3.0

    # Second pit stop at lap 10
    assert pit_stops.iloc[1]["LapNumber"] == 10
    assert pit_stops.iloc[1]["Duration"] == 3.0


def test_get_stints_dataframe() -> None:
    """Test getting stints as DataFrame."""
    laps = create_sample_driver_laps()
    stints_df = get_stints_dataframe(laps)

    assert not stints_df.empty
    assert len(stints_df) == 3
    assert "Driver" in stints_df.columns
    assert "StintNumber" in stints_df.columns
    assert "Compound" in stints_df.columns
    assert "LapStart" in stints_df.columns
    assert "LapEnd" in stints_df.columns


def test_empty_laps() -> None:
    """Test functions handle empty laps gracefully."""
    empty_laps = pd.DataFrame()

    stints = calculate_stints(empty_laps)
    assert len(stints) == 0

    pit_stops = get_pit_stops(empty_laps)
    assert pit_stops.empty

    stints_df = get_stints_dataframe(empty_laps)
    assert stints_df.empty


def test_single_stint() -> None:
    """Test with a race that has only one stint (no pit stops)."""
    laps = pd.DataFrame(
        {
            "Driver": ["HAM"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90) for _ in range(10)],
            "Compound": ["HARD"] * 10,
            "TyreLife": list(range(1, 11)),
            "Position": [1] * 10,
            "PitInTime": [None] * 10,
            "PitOutTime": [None] * 10,
        }
    )

    stints = calculate_stints(laps)
    assert len(stints) == 1
    assert stints[0].compound == "HARD"
    assert stints[0].laps_completed == 10

    pit_stops = get_pit_stops(laps)
    assert pit_stops.empty

