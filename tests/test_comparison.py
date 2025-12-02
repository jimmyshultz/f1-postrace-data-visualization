"""Tests for comparison analysis module."""

from datetime import timedelta

import pandas as pd

from analysis.comparison import (
    calculate_time_deltas,
    calculate_total_pit_time,
    compare_driver_pace,
    compare_stints,
    get_head_to_head_summary,
)


def create_driver_laps(
    driver: str, num_laps: int = 10, base_time: float = 90.0
) -> pd.DataFrame:
    """Create sample lap data for a driver."""
    # Create compound list based on num_laps
    if num_laps <= 5:
        compound = ["SOFT"] * num_laps
    else:
        soft_laps = min(5, num_laps)
        hard_laps = num_laps - soft_laps
        compound = ["SOFT"] * soft_laps + ["HARD"] * hard_laps

    # Create pit stop times based on num_laps
    pit_in = [None] * num_laps
    pit_out = [None] * num_laps
    if num_laps >= 5:
        pit_in[4] = pd.Timestamp("2024-01-01 12:00:00")
        pit_out[5] = pd.Timestamp("2024-01-01 12:00:03")

    return pd.DataFrame(
        {
            "Driver": [driver] * num_laps,
            "LapNumber": list(range(1, num_laps + 1)),
            "LapTime": [timedelta(seconds=base_time + i * 0.1) for i in range(num_laps)],
            "Compound": compound,
            "Position": [2] * num_laps,
            "PitInTime": pit_in,
            "PitOutTime": pit_out,
        }
    )


def test_compare_driver_pace() -> None:
    """Test pace comparison between two drivers."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    driver2_laps = create_driver_laps("HAM", num_laps=10, base_time=90.5)

    comparison = compare_driver_pace(driver1_laps, driver2_laps)

    assert not comparison.empty
    assert len(comparison) > 0
    assert "LapNumber" in comparison.columns
    assert "Delta" in comparison.columns
    assert "Driver1Time" in comparison.columns
    assert "Driver2Time" in comparison.columns

    # VER should be faster (negative delta)
    assert comparison["Delta"].mean() < 0


def test_compare_driver_pace_different_lap_counts() -> None:
    """Test pace comparison when drivers complete different number of laps."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    driver2_laps = create_driver_laps("HAM", num_laps=8, base_time=90.5)

    comparison = compare_driver_pace(driver1_laps, driver2_laps)

    # Should only have comparison for common laps (1-8)
    assert len(comparison) <= 8


def test_compare_stints() -> None:
    """Test stint strategy comparison."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    driver2_laps = create_driver_laps("HAM", num_laps=10, base_time=90.5)

    stint_comparison = compare_stints(driver1_laps, driver2_laps)

    assert not stint_comparison.empty
    assert "Stint" in stint_comparison.columns
    # Should have columns for both drivers
    assert any("VER" in col for col in stint_comparison.columns)
    assert any("HAM" in col for col in stint_comparison.columns)


def test_calculate_time_deltas() -> None:
    """Test time delta calculations."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    driver2_laps = create_driver_laps("HAM", num_laps=10, base_time=91.0)

    deltas = calculate_time_deltas(driver1_laps, driver2_laps)

    assert "avg_delta" in deltas
    assert "median_delta" in deltas
    assert "fastest_lap_delta" in deltas
    assert "total_pit_time_delta" in deltas

    # VER faster, so deltas should be negative
    assert deltas["avg_delta"] < 0
    assert deltas["fastest_lap_delta"] < 0


def test_calculate_total_pit_time() -> None:
    """Test pit time calculation."""
    driver_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)

    pit_time = calculate_total_pit_time(driver_laps)

    # Should have pit time from the stop we created
    assert pit_time > 0


def test_get_head_to_head_summary() -> None:
    """Test comprehensive head-to-head summary."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    driver2_laps = create_driver_laps("HAM", num_laps=10, base_time=90.5)

    summary = get_head_to_head_summary("VER", driver1_laps, "HAM", driver2_laps)

    assert "driver1" in summary
    assert "driver2" in summary
    assert summary["driver1"] == "VER"
    assert summary["driver2"] == "HAM"
    assert "driver1_faster_laps" in summary
    assert "driver2_faster_laps" in summary
    assert "avg_pace_delta" in summary

    # VER should win more laps
    assert summary["driver1_faster_laps"] > 0


def test_empty_laps() -> None:
    """Test functions handle empty laps gracefully."""
    driver1_laps = create_driver_laps("VER", num_laps=10, base_time=90.0)
    empty_laps = pd.DataFrame()

    comparison = compare_driver_pace(driver1_laps, empty_laps)
    assert comparison.empty

    comparison = compare_driver_pace(empty_laps, driver1_laps)
    assert comparison.empty

    stint_comparison = compare_stints(driver1_laps, empty_laps)
    assert not stint_comparison.empty  # Should still show driver1's stints

    summary = get_head_to_head_summary("VER", driver1_laps, "HAM", empty_laps)
    assert summary == {}

