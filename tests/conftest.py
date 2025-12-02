"""Pytest configuration and shared fixtures."""

from datetime import timedelta

import pandas as pd
import pytest


@pytest.fixture
def sample_laps() -> pd.DataFrame:
    """Create sample lap data for testing."""
    return pd.DataFrame(
        {
            "Driver": ["VER"] * 10,
            "DriverNumber": [1] * 10,
            "Team": ["Red Bull Racing"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90 + i * 0.1) for i in range(10)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
            "TyreLife": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Position": [3, 3, 3, 3, 4, 3, 3, 2, 2, 2],
            "PitInTime": [None] * 4
            + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 5,
            "PitOutTime": [None] * 5
            + [pd.Timestamp("2024-01-01 12:00:03")]
            + [None] * 4,
            "TrackStatus": ["1"] * 10,
            "Sector1Time": [timedelta(seconds=30)] * 10,
            "Sector2Time": [timedelta(seconds=30)] * 10,
            "Sector3Time": [timedelta(seconds=30)] * 10,
        }
    )


@pytest.fixture
def sample_two_driver_laps() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create sample lap data for two drivers."""
    driver1_laps = pd.DataFrame(
        {
            "Driver": ["VER"] * 10,
            "DriverNumber": [1] * 10,
            "Team": ["Red Bull Racing"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90 + i * 0.1) for i in range(10)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
            "TyreLife": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Position": [2, 2, 2, 2, 2, 1, 1, 1, 1, 1],
            "PitInTime": [None] * 4
            + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 5,
            "PitOutTime": [None] * 5
            + [pd.Timestamp("2024-01-01 12:00:03")]
            + [None] * 4,
            "TrackStatus": ["1"] * 10,
        }
    )

    driver2_laps = pd.DataFrame(
        {
            "Driver": ["HAM"] * 10,
            "DriverNumber": [44] * 10,
            "Team": ["Mercedes"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90.5 + i * 0.1) for i in range(10)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
            "TyreLife": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "Position": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            "PitInTime": [None] * 4
            + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 5,
            "PitOutTime": [None] * 5
            + [pd.Timestamp("2024-01-01 12:00:02.5")]
            + [None] * 4,
            "TrackStatus": ["1"] * 10,
        }
    )

    return driver1_laps, driver2_laps

