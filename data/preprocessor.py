"""Data preprocessing and validation."""

import logging

import pandas as pd

from data.loader import SessionData

logger = logging.getLogger(__name__)


def filter_valid_laps(laps_df: pd.DataFrame, remove_pit_laps: bool = True) -> pd.DataFrame:
    """
    Filter out invalid laps.

    Args:
        laps_df: DataFrame of laps
        remove_pit_laps: Whether to remove pit in/out laps

    Returns:
        Filtered DataFrame with only valid laps
    """
    if laps_df.empty:
        return laps_df

    valid_laps = laps_df.copy()

    # Remove laps with no lap time
    valid_laps = valid_laps[valid_laps["LapTime"].notna()]

    if remove_pit_laps:
        # Remove laps where driver pitted
        valid_laps = valid_laps[
            (valid_laps["PitOutTime"].isna()) & (valid_laps["PitInTime"].isna())
        ]

    logger.debug(
        f"Filtered laps: {len(laps_df)} -> {len(valid_laps)} "
        f"({len(laps_df) - len(valid_laps)} removed)"
    )

    return valid_laps


def get_clean_laps(
    laps_df: pd.DataFrame, remove_outliers: bool = True, std_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Get clean laps suitable for analysis (no yellows, traffic, etc.).

    Args:
        laps_df: DataFrame of laps
        remove_outliers: Whether to remove statistical outliers
        std_threshold: Number of standard deviations for outlier detection

    Returns:
        DataFrame of clean laps
    """
    clean_laps = filter_valid_laps(laps_df, remove_pit_laps=True)

    if clean_laps.empty:
        return clean_laps

    # Remove laps with track status issues if available
    if "TrackStatus" in clean_laps.columns:
        # TrackStatus: 1 = clear, 2 = yellow, 4 = safety car, 5 = red flag, 6 = VSC
        clean_laps = clean_laps[clean_laps["TrackStatus"] == "1"]

    # Remove outliers based on lap time
    if remove_outliers and len(clean_laps) > 3:
        lap_times = clean_laps["LapTime"].apply(lambda x: x.total_seconds())
        mean_time = lap_times.mean()
        std_time = lap_times.std()

        # Keep laps within threshold standard deviations
        lower_bound = mean_time - (std_threshold * std_time)
        upper_bound = mean_time + (std_threshold * std_time)

        clean_laps = clean_laps[
            (lap_times >= lower_bound) & (lap_times <= upper_bound)
        ]

    logger.debug(f"Clean laps: {len(laps_df)} -> {len(clean_laps)}")

    return clean_laps


def validate_session_data(session_data: SessionData) -> bool:
    """
    Validate that session data is complete and usable.

    Args:
        session_data: Loaded session data

    Returns:
        True if valid, False otherwise
    """
    if session_data is None:
        logger.error("Session data is None")
        return False

    if session_data.laps.empty:
        logger.error("Session has no lap data")
        return False

    if len(session_data.drivers) == 0:
        logger.error("Session has no drivers")
        return False

    # Check for minimum lap count
    min_laps = 10  # Reasonable minimum for analysis
    if len(session_data.laps) < min_laps:
        logger.warning(
            f"Session has only {len(session_data.laps)} laps (minimum {min_laps})"
        )
        return False

    # Check for required columns
    required_columns = [
        "Driver",
        "LapNumber",
        "LapTime",
        "Compound",
    ]
    missing_columns = [col for col in required_columns if col not in session_data.laps.columns]

    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False

    logger.info("Session data validation passed")
    return True


def get_driver_stint_data(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group laps by stint (consecutive laps on same compound).

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        DataFrame with stint grouping added
    """
    if laps_df.empty:
        return laps_df

    laps_copy = laps_df.copy()

    # Detect compound changes to identify stints
    laps_copy["StintNumber"] = (
        laps_copy["Compound"] != laps_copy["Compound"].shift()
    ).cumsum()

    return laps_copy


def extract_pit_stops(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract pit stop information from laps.

    Args:
        laps_df: DataFrame of laps

    Returns:
        DataFrame with pit stop information
    """
    if laps_df.empty:
        return pd.DataFrame(columns=["LapNumber", "PitInTime", "PitOutTime", "PitDuration"])

    # Find laps where driver pitted
    pit_laps = laps_df[laps_df["PitInTime"].notna()].copy()

    if pit_laps.empty:
        return pd.DataFrame(columns=["LapNumber", "PitInTime", "PitOutTime", "PitDuration"])

    # Calculate pit duration if both in and out times available
    if "PitOutTime" in pit_laps.columns:
        pit_laps["PitDuration"] = pit_laps.apply(
            lambda row: (row["PitOutTime"] - row["PitInTime"]).total_seconds()
            if pd.notna(row["PitOutTime"])
            else None,
            axis=1,
        )

    pit_stops = pit_laps[["LapNumber", "PitInTime", "PitOutTime", "PitDuration"]].copy()

    return pit_stops

