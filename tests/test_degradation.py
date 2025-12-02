"""Tests for degradation analysis module."""

from datetime import timedelta

import pandas as pd

from analysis.degradation import (
    analyze_stint_degradation,
    calculate_degradation_rate,
    detect_cliff,
    get_stint_degradation_summary,
)


def create_degrading_laps(
    num_laps: int = 10, initial_time: float = 90.0, deg_rate: float = 0.1
) -> pd.DataFrame:
    """Create sample laps with linear degradation."""
    laps = []
    for i in range(num_laps):
        lap_time = initial_time + (deg_rate * i)
        laps.append(
            {
                "Driver": "VER",
                "LapNumber": i + 1,
                "LapTime": timedelta(seconds=lap_time),
                "Compound": "MEDIUM",
                "Position": 1,
                "PitInTime": None,
                "PitOutTime": None,
                "TrackStatus": "1",
            }
        )

    return pd.DataFrame(laps)


def test_calculate_degradation_rate() -> None:
    """Test degradation rate calculation."""
    # Create laps with 0.1s/lap degradation
    laps = create_degrading_laps(num_laps=10, initial_time=90.0, deg_rate=0.1)

    deg_rate, r_squared = calculate_degradation_rate(laps, use_clean_laps=False)

    # Should be close to 0.1 s/lap
    assert abs(deg_rate - 0.1) < 0.01

    # Should have good fit
    assert r_squared > 0.95


def test_calculate_degradation_rate_no_degradation() -> None:
    """Test with constant lap times (no degradation)."""
    laps = create_degrading_laps(num_laps=10, initial_time=90.0, deg_rate=0.0)

    deg_rate, r_squared = calculate_degradation_rate(laps, use_clean_laps=False)

    # Should be close to 0
    assert abs(deg_rate) < 0.01


def test_analyze_stint_degradation() -> None:
    """Test stint degradation analysis."""
    laps = create_degrading_laps(num_laps=10, initial_time=90.0, deg_rate=0.2)

    metrics = analyze_stint_degradation("VER", 1, laps)

    assert metrics is not None
    assert metrics.driver == "VER"
    assert metrics.stint_number == 1
    assert metrics.compound == "MEDIUM"
    assert len(metrics.lap_times) > 0
    assert metrics.initial_pace > 0
    assert metrics.final_pace > metrics.initial_pace  # Should degrade
    assert metrics.degradation_rate > 0


def test_analyze_stint_degradation_insufficient_laps() -> None:
    """Test with too few laps."""
    laps = create_degrading_laps(num_laps=2)

    metrics = analyze_stint_degradation("VER", 1, laps)

    # Should return None for insufficient data
    assert metrics is None


def test_detect_cliff() -> None:
    """Test cliff detection."""
    # Create laps with sudden time increase at lap 6
    laps = []
    for i in range(10):
        if i < 5:
            lap_time = 90.0
        else:
            lap_time = 91.5  # Sudden 1.5s jump

        laps.append(
            {
                "LapNumber": i + 1,
                "LapTime": timedelta(seconds=lap_time),
            }
        )

    laps_df = pd.DataFrame(laps)

    cliff_lap = detect_cliff(laps_df, threshold=0.5)

    # Should detect cliff at lap 6
    assert cliff_lap == 6


def test_detect_cliff_no_cliff() -> None:
    """Test with no cliff present."""
    laps = create_degrading_laps(num_laps=10, deg_rate=0.1)

    cliff_lap = detect_cliff(laps, threshold=0.5)

    # Should not detect any cliff
    assert cliff_lap is None


def test_get_stint_degradation_summary() -> None:
    """Test getting degradation summary for all stints."""
    # Create laps with two stints
    laps_stint1 = create_degrading_laps(num_laps=10, initial_time=90.0, deg_rate=0.2)
    laps_stint1["Compound"] = "SOFT"

    laps_stint2 = create_degrading_laps(num_laps=10, initial_time=92.0, deg_rate=0.1)
    laps_stint2["Compound"] = "HARD"
    laps_stint2["LapNumber"] = range(11, 21)

    all_laps = pd.concat([laps_stint1, laps_stint2], ignore_index=True)

    summary = get_stint_degradation_summary(all_laps)

    assert not summary.empty
    assert len(summary) == 2  # Two stints
    assert "Stint" in summary.columns
    assert "Compound" in summary.columns
    assert "Degradation" in summary.columns


def test_empty_dataframe() -> None:
    """Test functions handle empty dataframes."""
    empty_df = pd.DataFrame()

    deg_rate, r_squared = calculate_degradation_rate(empty_df)
    assert deg_rate == 0.0
    assert r_squared == 0.0

    metrics = analyze_stint_degradation("VER", 1, empty_df)
    assert metrics is None

    summary = get_stint_degradation_summary(empty_df)
    assert summary.empty

