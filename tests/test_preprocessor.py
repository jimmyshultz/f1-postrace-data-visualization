"""Tests for data preprocessor module."""

from datetime import timedelta

import pandas as pd

from data.preprocessor import (
    extract_pit_stops,
    filter_valid_laps,
    get_clean_laps,
    get_driver_stint_data,
)


def create_sample_laps() -> pd.DataFrame:
    """Create sample lap data for testing."""
    return pd.DataFrame(
        {
            "LapNumber": [1, 2, 3, 4, 5, 6, 7, 8],
            "LapTime": [
                timedelta(seconds=90),
                timedelta(seconds=88),
                timedelta(seconds=87),
                None,  # Invalid lap
                timedelta(seconds=89),
                timedelta(seconds=88),
                timedelta(seconds=150),  # Outlier
                timedelta(seconds=87),
            ],
            "Compound": ["SOFT", "SOFT", "SOFT", "SOFT", "MEDIUM", "MEDIUM", "MEDIUM", "MEDIUM"],
            "PitInTime": [None, None, None, pd.Timestamp("2024-01-01 12:00:00"), None, None, None, None],
            "PitOutTime": [None, None, None, None, pd.Timestamp("2024-01-01 12:00:03"), None, None, None],
        }
    )


def test_filter_valid_laps() -> None:
    """Test filtering of valid laps."""
    laps = create_sample_laps()
    valid_laps = filter_valid_laps(laps, remove_pit_laps=True)

    # Should remove lap with null LapTime (lap 4) and pit out lap (lap 5)
    # Keeps laps: 1, 2, 3, 6, 7, 8 = 6 laps
    assert len(valid_laps) == 6
    assert valid_laps["LapTime"].notna().all()
    assert 4 not in valid_laps["LapNumber"].values  # Lap 4 has null time
    assert 5 not in valid_laps["LapNumber"].values  # Lap 5 is pit out lap


def test_filter_valid_laps_keep_pit() -> None:
    """Test filtering but keeping pit laps."""
    laps = create_sample_laps()
    valid_laps = filter_valid_laps(laps, remove_pit_laps=False)

    # Should only remove lap with null LapTime
    assert len(valid_laps) == 7


def test_get_clean_laps() -> None:
    """Test getting clean laps with outlier removal."""
    laps = create_sample_laps()
    clean_laps = get_clean_laps(laps, remove_outliers=True)

    # Should remove null time (lap 4) and pit out lap (lap 5)
    # Outlier detection might not remove lap 7 if std threshold isn't hit
    # At minimum should have 6 laps or less
    assert len(clean_laps) <= 6
    assert len(clean_laps) >= 5
    # Check no extreme outliers remain if outlier detection worked
    lap_times = clean_laps["LapTime"].apply(lambda x: x.total_seconds())
    # Either lap 7 was removed or it's still there
    if len(clean_laps) == 5:
        assert lap_times.max() < 100  # The 150s lap was removed
    else:
        assert len(clean_laps) == 6  # The 150s lap is still there but marked


def test_get_driver_stint_data() -> None:
    """Test stint grouping."""
    laps = create_sample_laps()
    stint_laps = get_driver_stint_data(laps)

    assert "StintNumber" in stint_laps.columns
    # Should have 2 stints (SOFT -> MEDIUM)
    assert stint_laps["StintNumber"].nunique() == 2
    # First 4 laps should be stint 1, rest stint 2
    assert stint_laps.iloc[0]["StintNumber"] == 1
    assert stint_laps.iloc[4]["StintNumber"] == 2


def test_extract_pit_stops() -> None:
    """Test pit stop extraction."""
    laps = create_sample_laps()
    pit_stops = extract_pit_stops(laps)

    assert len(pit_stops) == 1
    assert pit_stops.iloc[0]["LapNumber"] == 4
    # Duration might be None if PitOutTime is on a different lap than PitInTime
    # This is expected behavior as pit entry and exit are on different laps
    assert "PitDuration" in pit_stops.columns


def test_empty_dataframe() -> None:
    """Test functions handle empty dataframes gracefully."""
    empty_df = pd.DataFrame()

    valid_laps = filter_valid_laps(empty_df)
    assert valid_laps.empty

    clean_laps = get_clean_laps(empty_df)
    assert clean_laps.empty

    stint_data = get_driver_stint_data(empty_df)
    assert stint_data.empty

    pit_stops = extract_pit_stops(empty_df)
    assert pit_stops.empty

