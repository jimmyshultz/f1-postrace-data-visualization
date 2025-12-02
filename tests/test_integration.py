"""Integration tests for the full analysis pipeline."""

import pandas as pd
import pytest

from analysis.comparison import get_head_to_head_summary
from analysis.degradation import get_stint_degradation_summary
from analysis.strategy import calculate_stints, get_pit_stops
from visualization.degradation_chart import create_degradation_chart
from visualization.tire_timeline import create_tire_timeline


def test_full_single_driver_analysis(sample_laps: pd.DataFrame) -> None:
    """Test complete analysis pipeline for single driver."""
    # 1. Calculate stints
    stints = calculate_stints(sample_laps)
    assert len(stints) > 0

    # 2. Get pit stops
    pit_stops = get_pit_stops(sample_laps)
    assert not pit_stops.empty

    # 3. Calculate degradation
    deg_summary = get_stint_degradation_summary(sample_laps)
    assert not deg_summary.empty

    # 4. Create visualizations
    timeline_fig = create_tire_timeline([("VER", sample_laps)], race_distance=10)
    assert timeline_fig is not None
    assert len(timeline_fig.data) > 0

    deg_fig = create_degradation_chart([("VER", sample_laps, "#3671C6")])
    assert deg_fig is not None
    assert len(deg_fig.data) > 0


def test_full_comparison_analysis(
    sample_two_driver_laps: tuple[pd.DataFrame, pd.DataFrame]
) -> None:
    """Test complete comparison pipeline for two drivers."""
    driver1_laps, driver2_laps = sample_two_driver_laps

    # 1. Get stints for both
    stints1 = calculate_stints(driver1_laps)
    stints2 = calculate_stints(driver2_laps)
    assert len(stints1) > 0
    assert len(stints2) > 0

    # 2. Head-to-head comparison
    summary = get_head_to_head_summary("VER", driver1_laps, "HAM", driver2_laps)
    assert summary is not None
    assert "driver1_faster_laps" in summary
    assert "driver2_faster_laps" in summary

    # 3. Create comparison visualizations
    timeline_fig = create_tire_timeline(
        [("VER", driver1_laps), ("HAM", driver2_laps)], race_distance=10
    )
    assert timeline_fig is not None
    assert len(timeline_fig.data) > 0

    deg_fig = create_degradation_chart(
        [("VER", driver1_laps, "#3671C6"), ("HAM", driver2_laps, "#27F4D2")]
    )
    assert deg_fig is not None
    assert len(deg_fig.data) > 0


def test_stint_to_visualization_pipeline(sample_laps: pd.DataFrame) -> None:
    """Test that stint calculation produces valid visualization input."""
    stints = calculate_stints(sample_laps)

    # Verify stint data is usable for visualization
    for stint in stints:
        assert stint.lap_start > 0
        assert stint.lap_end >= stint.lap_start
        assert stint.laps_completed > 0
        assert stint.compound in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]


def test_degradation_calculation_pipeline(sample_laps: pd.DataFrame) -> None:
    """Test degradation calculation produces valid metrics."""
    deg_summary = get_stint_degradation_summary(sample_laps)

    assert not deg_summary.empty
    assert "Stint" in deg_summary.columns
    assert "Compound" in deg_summary.columns
    assert "Degradation" in deg_summary.columns


@pytest.mark.slow
def test_real_session_integration() -> None:
    """
    Integration test with real F1 data.

    This test requires network access and is marked as slow.
    It tests the complete workflow with actual FastF1 data.
    """
    from data.loader import load_session
    from data.preprocessor import validate_session_data

    # Load a known good session
    session_data = load_session(2024, "Bahrain Grand Prix", "R")

    # Verify session loaded correctly
    assert session_data is not None
    assert validate_session_data(session_data)

    # Get a driver's laps
    assert len(session_data.drivers) > 0
    test_driver = session_data.drivers[0]

    driver_laps = session_data.laps.pick_drivers(test_driver)
    assert not driver_laps.empty

    # Run full analysis
    stints = calculate_stints(driver_laps)
    assert len(stints) > 0

    # Call these functions to verify they don't error (results may be empty)
    get_pit_stops(driver_laps)
    get_stint_degradation_summary(driver_laps)

    # Create visualizations
    timeline_fig = create_tire_timeline(
        [(test_driver, driver_laps)], race_distance=session_data.race_distance
    )
    assert timeline_fig is not None

    deg_fig = create_degradation_chart([(test_driver, driver_laps, None)])
    assert deg_fig is not None

