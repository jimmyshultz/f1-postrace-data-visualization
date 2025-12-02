"""Tire degradation analysis functions."""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from data.preprocessor import get_clean_laps

logger = logging.getLogger(__name__)


@dataclass
class DegradationMetrics:
    """Tire degradation analysis results."""

    driver: str
    compound: str
    stint_number: int
    lap_times: List[float]
    lap_numbers: List[int]
    initial_pace: float
    final_pace: float
    degradation_rate: float  # seconds per lap
    total_degradation: float  # total time lost
    r_squared: float  # regression quality
    cliff_lap: Optional[int] = None


def calculate_degradation_rate(
    laps_df: pd.DataFrame, use_clean_laps: bool = True
) -> Tuple[float, float]:
    """
    Calculate tire degradation rate using linear regression.

    Args:
        laps_df: DataFrame of laps for a stint
        use_clean_laps: Whether to filter for clean laps only

    Returns:
        Tuple of (degradation_rate, r_squared)
        degradation_rate: seconds per lap
        r_squared: regression quality (0-1)
    """
    if laps_df.empty:
        return 0.0, 0.0

    # Filter to clean laps if requested
    if use_clean_laps:
        laps_to_analyze = get_clean_laps(laps_df, remove_outliers=True)
    else:
        laps_to_analyze = laps_df[laps_df["LapTime"].notna()]

    if len(laps_to_analyze) < 3:
        logger.debug("Not enough laps for degradation calculation")
        return 0.0, 0.0

    # Extract lap numbers and times
    lap_numbers = laps_to_analyze["LapNumber"].values
    lap_times = laps_to_analyze["LapTime"].apply(lambda x: x.total_seconds()).values

    # Perform linear regression
    # y = mx + b where m is the degradation rate
    coefficients = np.polyfit(lap_numbers, lap_times, 1)
    degradation_rate = coefficients[0]  # slope

    # Calculate R-squared
    y_pred = np.polyval(coefficients, lap_numbers)
    ss_res = np.sum((lap_times - y_pred) ** 2)
    ss_tot = np.sum((lap_times - np.mean(lap_times)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    logger.debug(
        f"Degradation rate: {degradation_rate:.4f} s/lap, R²: {r_squared:.4f}"
    )

    return degradation_rate, r_squared


def analyze_stint_degradation(
    driver: str, stint_number: int, stint_laps: pd.DataFrame
) -> Optional[DegradationMetrics]:
    """
    Analyze degradation for a single stint.

    Args:
        driver: Driver name
        stint_number: Stint number
        stint_laps: DataFrame of laps in the stint

    Returns:
        DegradationMetrics object or None if analysis fails
    """
    if stint_laps.empty or len(stint_laps) < 3:
        return None

    # Get compound
    compound = stint_laps.iloc[0].get("Compound", "UNKNOWN")

    # Get clean laps for analysis
    clean_laps = get_clean_laps(stint_laps, remove_outliers=True)

    if len(clean_laps) < 3:
        logger.debug(f"Not enough clean laps for {driver} stint {stint_number}")
        return None

    # Calculate degradation rate
    deg_rate, r_squared = calculate_degradation_rate(stint_laps, use_clean_laps=True)

    # Extract lap times and numbers
    lap_numbers = clean_laps["LapNumber"].tolist()
    lap_times = clean_laps["LapTime"].apply(lambda x: x.total_seconds()).tolist()

    initial_pace = lap_times[0] if lap_times else 0.0
    final_pace = lap_times[-1] if lap_times else 0.0
    total_degradation = final_pace - initial_pace

    # Detect cliff (optional for MVP)
    cliff_lap = detect_cliff(clean_laps)

    return DegradationMetrics(
        driver=driver,
        compound=compound,
        stint_number=stint_number,
        lap_times=lap_times,
        lap_numbers=lap_numbers,
        initial_pace=initial_pace,
        final_pace=final_pace,
        degradation_rate=deg_rate,
        total_degradation=total_degradation,
        r_squared=r_squared,
        cliff_lap=cliff_lap,
    )


def detect_cliff(laps_df: pd.DataFrame, threshold: float = 0.5) -> Optional[int]:
    """
    Detect if there's a "cliff" - sudden degradation acceleration.

    Args:
        laps_df: DataFrame of laps
        threshold: Threshold for detecting cliff (seconds increase)

    Returns:
        Lap number where cliff occurs, or None
    """
    if len(laps_df) < 5:
        return None

    lap_times = laps_df["LapTime"].apply(lambda x: x.total_seconds()).values

    # Calculate rolling difference
    for i in range(1, len(lap_times) - 1):
        time_jump = lap_times[i] - lap_times[i - 1]
        if time_jump > threshold:
            return int(laps_df.iloc[i]["LapNumber"])

    return None


def get_stint_degradation_summary(
    driver_laps: pd.DataFrame,
) -> pd.DataFrame:
    """
    Get degradation summary for all stints of a driver.

    Args:
        driver_laps: DataFrame of all laps for a driver

    Returns:
        DataFrame with degradation metrics per stint
    """
    from data.preprocessor import get_driver_stint_data

    # Add stint numbers
    stint_laps = get_driver_stint_data(driver_laps)

    if stint_laps.empty:
        return pd.DataFrame()

    driver = stint_laps.iloc[0].get("Driver", "Unknown")
    stint_numbers = stint_laps["StintNumber"].unique()

    summaries = []

    for stint_num in stint_numbers:
        stint_data = stint_laps[stint_laps["StintNumber"] == stint_num]
        metrics = analyze_stint_degradation(driver, stint_num, stint_data)

        if metrics:
            summaries.append(
                {
                    "Stint": stint_num,
                    "Compound": metrics.compound,
                    "Laps": len(stint_data),
                    "Initial Pace": f"{metrics.initial_pace:.3f}s",
                    "Final Pace": f"{metrics.final_pace:.3f}s",
                    "Degradation": f"{metrics.degradation_rate:.4f}s/lap",
                    "Total Loss": f"{metrics.total_degradation:.3f}s",
                    "R²": f"{metrics.r_squared:.3f}",
                }
            )

    return pd.DataFrame(summaries)


def filter_clean_laps_for_chart(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter laps for chart display - less aggressive than analysis filtering.

    Args:
        laps_df: DataFrame of laps

    Returns:
        Filtered laps suitable for visualization
    """
    if laps_df.empty:
        return laps_df

    # Remove pit laps but keep more laps for visualization
    clean = laps_df[
        (laps_df["PitInTime"].isna())
        & (laps_df["PitOutTime"].isna())
        & (laps_df["LapTime"].notna())
    ].copy()

    return clean

