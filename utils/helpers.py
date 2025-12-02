"""Common utility functions."""

from datetime import timedelta
from typing import Optional

import pandas as pd


def format_laptime(laptime: Optional[timedelta]) -> str:
    """
    Format a lap time as MM:SS.mmm.

    Args:
        laptime: Timedelta representing lap time

    Returns:
        Formatted string like "1:23.456"
    """
    if laptime is None or pd.isna(laptime):
        return "N/A"

    if isinstance(laptime, timedelta):
        total_seconds = laptime.total_seconds()
    else:
        total_seconds = float(laptime)

    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60

    return f"{minutes}:{seconds:06.3f}"


def format_time_delta(delta: Optional[timedelta]) -> str:
    """
    Format a time delta with +/- sign.

    Args:
        delta: Timedelta to format

    Returns:
        Formatted string like "+0.234" or "-1.567"
    """
    if delta is None or pd.isna(delta):
        return "N/A"

    if isinstance(delta, timedelta):
        seconds = delta.total_seconds()
    else:
        seconds = float(delta)

    sign = "+" if seconds >= 0 else ""
    return f"{sign}{seconds:.3f}"


def calculate_average_laptime(lap_times: pd.Series) -> Optional[timedelta]:
    """
    Calculate average lap time from a series of lap times.

    Args:
        lap_times: Series of lap times

    Returns:
        Average lap time as timedelta, or None if no valid laps
    """
    valid_laps = lap_times.dropna()
    if len(valid_laps) == 0:
        return None

    # Convert to seconds, calculate mean, convert back
    if isinstance(valid_laps.iloc[0], timedelta):
        avg_seconds = valid_laps.apply(lambda x: x.total_seconds()).mean()
        return timedelta(seconds=avg_seconds)
    else:
        return timedelta(seconds=valid_laps.mean())


def filter_valid_laps(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out invalid laps (pit laps, incomplete laps).

    Args:
        laps_df: DataFrame of laps

    Returns:
        Filtered DataFrame with only valid laps
    """
    if laps_df.empty:
        return laps_df

    # Remove laps where:
    # - PitOutTime or PitInTime is not null (pit laps)
    # - LapTime is null
    # - Accuracy issues flagged
    valid_laps = laps_df[
        (laps_df["PitOutTime"].isna())
        & (laps_df["PitInTime"].isna())
        & (laps_df["LapTime"].notna())
    ].copy()

    return valid_laps


def get_position_change(laps_df: pd.DataFrame) -> int:
    """
    Calculate position change during a stint or period.

    Args:
        laps_df: DataFrame of laps with Position column

    Returns:
        Position change (negative means gained positions)
    """
    if laps_df.empty or "Position" not in laps_df.columns:
        return 0

    start_pos = laps_df.iloc[0]["Position"]
    end_pos = laps_df.iloc[-1]["Position"]

    if pd.isna(start_pos) or pd.isna(end_pos):
        return 0

    return int(end_pos - start_pos)

