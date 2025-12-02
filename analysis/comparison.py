"""Driver comparison analysis functions."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compare_driver_pace(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare pace between two drivers on a lap-by-lap basis.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        DataFrame with lap-by-lap delta comparison
    """
    if driver1_laps.empty or driver2_laps.empty:
        return pd.DataFrame()

    # Find common laps (where both have data)
    common_laps = set(driver1_laps["LapNumber"]) & set(driver2_laps["LapNumber"])

    if not common_laps:
        return pd.DataFrame()

    deltas = []

    for lap_num in sorted(common_laps):
        lap1 = driver1_laps[driver1_laps["LapNumber"] == lap_num].iloc[0]
        lap2 = driver2_laps[driver2_laps["LapNumber"] == lap_num].iloc[0]

        # Skip if either lap has no time
        if pd.isna(lap1.get("LapTime")) or pd.isna(lap2.get("LapTime")):
            continue

        time1 = lap1["LapTime"].total_seconds()
        time2 = lap2["LapTime"].total_seconds()
        delta = time1 - time2  # Positive means driver1 slower

        deltas.append(
            {
                "LapNumber": lap_num,
                "Driver1Time": time1,
                "Driver2Time": time2,
                "Delta": delta,
                "Driver1Compound": lap1.get("Compound"),
                "Driver2Compound": lap2.get("Compound"),
            }
        )

    return pd.DataFrame(deltas)


def compare_stints(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare stint strategies between two drivers.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        DataFrame comparing stint strategies
    """
    from analysis.strategy import calculate_stints

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    stints1 = calculate_stints(driver1_laps)
    stints2 = calculate_stints(driver2_laps)

    comparison = []

    max_stints = max(len(stints1), len(stints2))

    for i in range(max_stints):
        stint1 = stints1[i] if i < len(stints1) else None
        stint2 = stints2[i] if i < len(stints2) else None

        comparison.append(
            {
                "Stint": i + 1,
                f"{driver1} Compound": stint1.compound if stint1 else "N/A",
                f"{driver1} Laps": stint1.laps_completed if stint1 else 0,
                f"{driver2} Compound": stint2.compound if stint2 else "N/A",
                f"{driver2} Laps": stint2.laps_completed if stint2 else 0,
                "Compound Match": stint1.compound == stint2.compound
                if stint1 and stint2
                else False,
            }
        )

    return pd.DataFrame(comparison)


def calculate_time_deltas(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> dict:
    """
    Calculate overall time differences between drivers.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        Dictionary with time delta statistics
    """
    pace_comparison = compare_driver_pace(driver1_laps, driver2_laps)

    if pace_comparison.empty:
        return {
            "avg_delta": 0.0,
            "median_delta": 0.0,
            "fastest_lap_delta": 0.0,
            "total_pit_time_delta": 0.0,
        }

    avg_delta = pace_comparison["Delta"].mean()
    median_delta = pace_comparison["Delta"].median()

    # Fastest lap comparison
    fastest1 = driver1_laps["LapTime"].min().total_seconds() if not driver1_laps.empty else 0
    fastest2 = driver2_laps["LapTime"].min().total_seconds() if not driver2_laps.empty else 0
    fastest_lap_delta = fastest1 - fastest2

    # Pit stop time comparison
    pit_time1 = calculate_total_pit_time(driver1_laps)
    pit_time2 = calculate_total_pit_time(driver2_laps)
    pit_time_delta = pit_time1 - pit_time2

    return {
        "avg_delta": avg_delta,
        "median_delta": median_delta,
        "fastest_lap_delta": fastest_lap_delta,
        "total_pit_time_delta": pit_time_delta,
    }


def calculate_total_pit_time(laps_df: pd.DataFrame) -> float:
    """
    Calculate total time spent in pit stops.

    Args:
        laps_df: Laps DataFrame

    Returns:
        Total pit time in seconds
    """
    from analysis.strategy import get_pit_stops

    pit_stops = get_pit_stops(laps_df)

    if pit_stops.empty or "Duration" not in pit_stops.columns:
        return 0.0

    total_time = pit_stops["Duration"].sum()

    return float(total_time) if not pd.isna(total_time) else 0.0


def get_head_to_head_summary(
    driver1: str,
    driver1_laps: pd.DataFrame,
    driver2: str,
    driver2_laps: pd.DataFrame,
) -> dict:
    """
    Get comprehensive head-to-head comparison summary.

    Args:
        driver1: First driver name
        driver1_laps: Laps for first driver
        driver2: Second driver name
        driver2_laps: Laps for second driver

    Returns:
        Dictionary with comparison summary
    """
    if driver1_laps.empty or driver2_laps.empty:
        return {}

    pace_comparison = compare_driver_pace(driver1_laps, driver2_laps)

    # Count laps where each driver was faster
    if not pace_comparison.empty:
        driver1_faster = (pace_comparison["Delta"] < 0).sum()
        driver2_faster = (pace_comparison["Delta"] > 0).sum()
        equal = (pace_comparison["Delta"] == 0).sum()
    else:
        driver1_faster = driver2_faster = equal = 0

    # Get time deltas
    deltas = calculate_time_deltas(driver1_laps, driver2_laps)

    # Get final positions
    pos1 = driver1_laps.iloc[-1].get("Position")
    pos2 = driver2_laps.iloc[-1].get("Position")

    return {
        "driver1": driver1,
        "driver2": driver2,
        "driver1_position": int(pos1) if pd.notna(pos1) else "N/A",
        "driver2_position": int(pos2) if pd.notna(pos2) else "N/A",
        "driver1_faster_laps": driver1_faster,
        "driver2_faster_laps": driver2_faster,
        "equal_laps": equal,
        "avg_pace_delta": deltas["avg_delta"],
        "median_pace_delta": deltas["median_delta"],
        "fastest_lap_delta": deltas["fastest_lap_delta"],
        "pit_time_delta": deltas["total_pit_time_delta"],
    }

