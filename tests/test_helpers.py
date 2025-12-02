"""Tests for helper utility functions."""

from datetime import timedelta

import pandas as pd

from utils.helpers import (
    calculate_average_laptime,
    filter_valid_laps,
    format_laptime,
    format_time_delta,
    get_position_change,
)


def test_format_laptime() -> None:
    """Test lap time formatting."""
    # Test normal lap time
    laptime = timedelta(seconds=83.456)
    formatted = format_laptime(laptime)
    assert formatted == "1:23.456"

    # Test time over 2 minutes
    laptime = timedelta(seconds=125.789)
    formatted = format_laptime(laptime)
    assert formatted == "2:05.789"

    # Test None
    formatted = format_laptime(None)
    assert formatted == "N/A"


def test_format_time_delta() -> None:
    """Test time delta formatting."""
    # Positive delta
    delta = timedelta(seconds=1.234)
    formatted = format_time_delta(delta)
    assert formatted == "+1.234"

    # Negative delta
    delta = timedelta(seconds=-0.567)
    formatted = format_time_delta(delta)
    assert formatted == "-0.567"

    # Zero
    delta = timedelta(seconds=0)
    formatted = format_time_delta(delta)
    assert formatted == "+0.000"

    # None
    formatted = format_time_delta(None)
    assert formatted == "N/A"


def test_calculate_average_laptime() -> None:
    """Test average lap time calculation."""
    lap_times = pd.Series(
        [
            timedelta(seconds=90.0),
            timedelta(seconds=90.5),
            timedelta(seconds=91.0),
        ]
    )

    avg = calculate_average_laptime(lap_times)
    assert avg is not None
    assert abs(avg.total_seconds() - 90.5) < 0.01

    # Test with None values
    lap_times_with_none = pd.Series([timedelta(seconds=90.0), None, timedelta(seconds=91.0)])
    avg = calculate_average_laptime(lap_times_with_none)
    assert avg is not None
    assert abs(avg.total_seconds() - 90.5) < 0.01

    # Test empty series
    empty_series = pd.Series([], dtype='object')
    avg = calculate_average_laptime(empty_series)
    assert avg is None


def test_filter_valid_laps() -> None:
    """Test valid lap filtering."""
    laps = pd.DataFrame(
        {
            "LapNumber": [1, 2, 3, 4, 5],
            "LapTime": [
                timedelta(seconds=90),
                None,
                timedelta(seconds=91),
                timedelta(seconds=92),
                timedelta(seconds=93),
            ],
            "PitInTime": [None, None, pd.Timestamp("2024-01-01"), None, None],
            "PitOutTime": [None, None, None, pd.Timestamp("2024-01-01"), None],
        }
    )

    valid = filter_valid_laps(laps)

    # Should keep laps 1 and 5 only (2 has no time, 3 and 4 are pit laps)
    assert len(valid) == 2
    assert 1 in valid["LapNumber"].values
    assert 5 in valid["LapNumber"].values


def test_get_position_change() -> None:
    """Test position change calculation."""
    laps = pd.DataFrame(
        {
            "Position": [5, 4, 4, 3, 2],  # Gained 3 positions
        }
    )

    change = get_position_change(laps)
    assert change == -3  # Negative means gained positions

    # Test position loss
    laps_loss = pd.DataFrame(
        {
            "Position": [2, 3, 4, 5],  # Lost 3 positions
        }
    )

    change = get_position_change(laps_loss)
    assert change == 3  # Positive means lost positions

    # Test empty
    empty = pd.DataFrame()
    change = get_position_change(empty)
    assert change == 0

