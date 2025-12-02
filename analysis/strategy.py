"""Tire strategy analysis functions."""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _hash_dataframe(df: pd.DataFrame) -> int:
    """Create a hash for DataFrame for caching purposes."""
    if df.empty:
        return 0
    # Use a combination of shape and sample values
    return hash((len(df), tuple(df.columns), df.iloc[0]["LapNumber"] if "LapNumber" in df.columns else 0))


@dataclass
class Stint:
    """Represents a tire stint."""

    driver: str
    stint_number: int
    compound: str
    lap_start: int
    lap_end: int
    tire_age_at_start: int
    laps_completed: int
    avg_lap_time: Optional[float] = None
    position_start: Optional[int] = None
    position_end: Optional[int] = None

    @property
    def position_change(self) -> int:
        """Calculate position change during stint (negative = gained positions)."""
        if self.position_start is not None and self.position_end is not None:
            return self.position_end - self.position_start
        return 0


def calculate_stints(laps_df: pd.DataFrame) -> List[Stint]:
    """
    Identify tire stints from lap data.

    A stint is a continuous period on the same tire compound.

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        List of Stint objects
    """
    start_time = time.perf_counter()

    if laps_df.empty:
        return []

    driver = laps_df.iloc[0]["Driver"] if "Driver" in laps_df.columns else "Unknown"
    stints: List[Stint] = []

    # Group by compound changes
    laps_df = laps_df.sort_values("LapNumber")
    current_compound = None
    stint_laps: List[pd.Series] = []
    stint_number = 0

    for idx, lap in laps_df.iterrows():
        compound = lap.get("Compound", "UNKNOWN")

        # Skip laps with no compound info
        if pd.isna(compound) or compound == "UNKNOWN":
            continue

        # Detect compound change (new stint)
        if compound != current_compound:
            # Save previous stint if exists
            if current_compound is not None and stint_laps:
                stint = _create_stint_from_laps(
                    driver, stint_number, current_compound, stint_laps
                )
                if stint:
                    stints.append(stint)

            # Start new stint
            stint_number += 1
            current_compound = compound
            stint_laps = [lap]
        else:
            stint_laps.append(lap)

    # Save final stint
    if stint_laps and current_compound:
        stint = _create_stint_from_laps(driver, stint_number, current_compound, stint_laps)
        if stint:
            stints.append(stint)

    elapsed = (time.perf_counter() - start_time) * 1000  # ms
    logger.debug(f"Calculated {len(stints)} stints for {driver} in {elapsed:.2f}ms")
    return stints


def _create_stint_from_laps(
    driver: str, stint_number: int, compound: str, laps: List[pd.Series]
) -> Optional[Stint]:
    """Create a Stint object from a list of laps."""
    if not laps:
        return None

    first_lap = laps[0]
    last_lap = laps[-1]

    # Calculate average lap time (excluding pit laps)
    valid_lap_times = [
        lap["LapTime"].total_seconds()
        for lap in laps
        if pd.notna(lap.get("LapTime"))
        and pd.isna(lap.get("PitInTime"))
        and pd.isna(lap.get("PitOutTime"))
    ]
    avg_lap_time = sum(valid_lap_times) / len(valid_lap_times) if valid_lap_times else None

    # Get tire age at start (if available)
    tire_age = int(first_lap.get("TyreLife", 0)) if "TyreLife" in first_lap else 0

    # Get positions
    position_start = first_lap.get("Position")
    position_end = last_lap.get("Position")

    return Stint(
        driver=driver,
        stint_number=stint_number,
        compound=compound,
        lap_start=int(first_lap["LapNumber"]),
        lap_end=int(last_lap["LapNumber"]),
        tire_age_at_start=tire_age,
        laps_completed=len(laps),
        avg_lap_time=avg_lap_time,
        position_start=int(position_start) if pd.notna(position_start) else None,
        position_end=int(position_end) if pd.notna(position_end) else None,
    )


def get_pit_stops(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract pit stop information from laps.

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        DataFrame with columns: LapNumber, PitInTime, PitOutTime, Duration
    """
    if laps_df.empty:
        return pd.DataFrame(columns=["LapNumber", "PitInTime", "PitOutTime", "Duration"])

    # Find laps where driver entered pit
    pit_laps = laps_df[laps_df["PitInTime"].notna()].copy()

    if pit_laps.empty:
        return pd.DataFrame(columns=["LapNumber", "PitInTime", "PitOutTime", "Duration"])

    # Calculate pit duration
    pit_stops = []
    for idx, lap in pit_laps.iterrows():
        # Try to find the corresponding out lap
        lap_number = lap["LapNumber"]
        next_laps = laps_df[laps_df["LapNumber"] > lap_number]

        out_lap = next_laps[next_laps["PitOutTime"].notna()].head(1)

        if not out_lap.empty:
            out_time = out_lap.iloc[0]["PitOutTime"]
            in_time = lap["PitInTime"]
            duration = (out_time - in_time).total_seconds() if pd.notna(out_time) else None
        else:
            duration = None

        pit_stops.append(
            {
                "LapNumber": lap_number,
                "PitInTime": lap["PitInTime"],
                "PitOutTime": out_lap.iloc[0]["PitOutTime"] if not out_lap.empty else None,
                "Duration": duration,
            }
        )

    return pd.DataFrame(pit_stops)


def get_stints_dataframe(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get stints as a DataFrame for easier manipulation.

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        DataFrame with stint information
    """
    stints = calculate_stints(laps_df)

    if not stints:
        return pd.DataFrame()

    stint_dicts = []
    for stint in stints:
        stint_dicts.append(
            {
                "Driver": stint.driver,
                "StintNumber": stint.stint_number,
                "Compound": stint.compound,
                "LapStart": stint.lap_start,
                "LapEnd": stint.lap_end,
                "TireAge": stint.tire_age_at_start,
                "LapsCompleted": stint.laps_completed,
                "AvgLapTime": stint.avg_lap_time,
                "PositionStart": stint.position_start,
                "PositionEnd": stint.position_end,
                "PositionChange": stint.position_change,
            }
        )

    return pd.DataFrame(stint_dicts)

