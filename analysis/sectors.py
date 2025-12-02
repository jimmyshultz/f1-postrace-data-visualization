"""Sector time comparison analysis functions."""

import logging
import time
from dataclasses import dataclass
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SectorSummary:
    """Summary statistics for a sector."""

    sector: int  # 1, 2, or 3
    best_time: float  # seconds
    avg_time: float  # seconds
    worst_time: float  # seconds
    std_dev: float  # consistency measure
    best_lap: int  # lap number with best sector time


def get_sector_times(laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract sector times from laps DataFrame.

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        DataFrame with lap number and sector times in seconds
    """
    if laps_df.empty:
        return pd.DataFrame(columns=["LapNumber", "Sector1", "Sector2", "Sector3"])

    sector_cols = ["Sector1Time", "Sector2Time", "Sector3Time"]
    if not all(col in laps_df.columns for col in sector_cols):
        logger.warning("Missing sector time columns in laps data")
        return pd.DataFrame(columns=["LapNumber", "Sector1", "Sector2", "Sector3"])

    result = laps_df[["LapNumber"]].copy()

    # Convert timedeltas to seconds
    for i, col in enumerate(sector_cols, start=1):
        result[f"Sector{i}"] = laps_df[col].apply(
            lambda x: x.total_seconds() if pd.notna(x) else None
        )

    # Include compound if available
    if "Compound" in laps_df.columns:
        result["Compound"] = laps_df["Compound"]

    return result


def get_sector_summary(laps_df: pd.DataFrame) -> List[SectorSummary]:
    """
    Calculate summary statistics for each sector.

    Args:
        laps_df: DataFrame of laps for a driver

    Returns:
        List of SectorSummary objects for each sector
    """
    sector_times = get_sector_times(laps_df)

    if sector_times.empty:
        return []

    summaries = []

    for sector_num in [1, 2, 3]:
        col = f"Sector{sector_num}"
        valid_times = sector_times[sector_times[col].notna()][col]

        if valid_times.empty:
            continue

        best_time = valid_times.min()
        best_lap_idx = valid_times.idxmin()
        best_lap = sector_times.loc[best_lap_idx, "LapNumber"]

        summaries.append(
            SectorSummary(
                sector=sector_num,
                best_time=float(best_time),
                avg_time=float(valid_times.mean()),
                worst_time=float(valid_times.max()),
                std_dev=float(valid_times.std()) if len(valid_times) > 1 else 0.0,
                best_lap=int(best_lap),
            )
        )

    return summaries


def get_sector_comparison(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare sector times between two drivers lap-by-lap.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        DataFrame with sector deltas (negative = driver1 faster)
    """
    start_time = time.perf_counter()

    if driver1_laps.empty or driver2_laps.empty:
        return pd.DataFrame()

    sector1_times = get_sector_times(driver1_laps)
    sector2_times = get_sector_times(driver2_laps)

    if sector1_times.empty or sector2_times.empty:
        return pd.DataFrame()

    # Find common laps
    common_laps = set(sector1_times["LapNumber"]) & set(sector2_times["LapNumber"])

    if not common_laps:
        return pd.DataFrame()

    comparisons = []

    for lap_num in sorted(common_laps):
        s1 = sector1_times[sector1_times["LapNumber"] == lap_num].iloc[0]
        s2 = sector2_times[sector2_times["LapNumber"] == lap_num].iloc[0]

        row = {"LapNumber": int(lap_num)}

        for sector in [1, 2, 3]:
            col = f"Sector{sector}"
            t1 = s1.get(col)
            t2 = s2.get(col)

            if pd.notna(t1) and pd.notna(t2):
                row[f"S{sector}_Driver1"] = t1
                row[f"S{sector}_Driver2"] = t2
                row[f"S{sector}_Delta"] = t1 - t2  # Negative = driver1 faster
            else:
                row[f"S{sector}_Driver1"] = None
                row[f"S{sector}_Driver2"] = None
                row[f"S{sector}_Delta"] = None

        # Calculate total delta for the lap
        total_delta = sum(
            row[f"S{s}_Delta"] for s in [1, 2, 3] if row[f"S{s}_Delta"] is not None
        )
        row["TotalDelta"] = total_delta if total_delta else None

        comparisons.append(row)

    elapsed = (time.perf_counter() - start_time) * 1000
    logger.debug(f"Sector comparison computed in {elapsed:.2f}ms")
    return pd.DataFrame(comparisons)


def identify_weak_sectors(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> dict:
    """
    Identify where each driver gains or loses time.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        Dictionary with sector advantage analysis
    """
    comparison = get_sector_comparison(driver1_laps, driver2_laps)

    if comparison.empty:
        return {
            "driver1_advantage_sectors": [],
            "driver2_advantage_sectors": [],
            "sector_deltas": {},
            "summary": "Insufficient data for sector comparison",
        }

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    sector_deltas = {}
    driver1_advantages = []
    driver2_advantages = []

    for sector in [1, 2, 3]:
        delta_col = f"S{sector}_Delta"
        valid_deltas = comparison[comparison[delta_col].notna()][delta_col]

        if valid_deltas.empty:
            continue

        avg_delta = valid_deltas.mean()
        sector_deltas[f"Sector{sector}"] = {
            "avg_delta": float(avg_delta),
            "driver1_faster_count": int((valid_deltas < 0).sum()),
            "driver2_faster_count": int((valid_deltas > 0).sum()),
            "laps_compared": len(valid_deltas),
        }

        # Determine who has advantage (threshold: 0.05s)
        if avg_delta < -0.05:
            driver1_advantages.append(sector)
        elif avg_delta > 0.05:
            driver2_advantages.append(sector)

    # Generate summary text
    summary_parts = []
    for sector in [1, 2, 3]:
        if f"Sector{sector}" in sector_deltas:
            delta = sector_deltas[f"Sector{sector}"]["avg_delta"]
            if abs(delta) >= 0.05:
                faster = driver1 if delta < 0 else driver2
                summary_parts.append(
                    f"{faster} gains {abs(delta):.3f}s avg in Sector {sector}"
                )

    return {
        "driver1": driver1,
        "driver2": driver2,
        "driver1_advantage_sectors": driver1_advantages,
        "driver2_advantage_sectors": driver2_advantages,
        "sector_deltas": sector_deltas,
        "summary": "; ".join(summary_parts) if summary_parts else "Sectors evenly matched",
    }


def get_sector_delta_by_compound(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> pd.DataFrame:
    """
    Get sector time comparison grouped by tire compound.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        DataFrame with average sector deltas per compound
    """
    if driver1_laps.empty or driver2_laps.empty:
        return pd.DataFrame()

    comparison = get_sector_comparison(driver1_laps, driver2_laps)

    if comparison.empty or "Compound" not in driver1_laps.columns:
        return pd.DataFrame()

    # Add compound info from driver1 (assuming same compound order)
    sector_times_1 = get_sector_times(driver1_laps)

    if sector_times_1.empty or "Compound" not in sector_times_1.columns:
        return pd.DataFrame()

    # Merge compound info
    comparison = comparison.merge(
        sector_times_1[["LapNumber", "Compound"]],
        on="LapNumber",
        how="left",
    )

    # Group by compound and calculate averages
    result_rows = []
    for compound in comparison["Compound"].dropna().unique():
        compound_data = comparison[comparison["Compound"] == compound]

        row = {"Compound": compound}
        for sector in [1, 2, 3]:
            delta_col = f"S{sector}_Delta"
            valid = compound_data[compound_data[delta_col].notna()][delta_col]
            row[f"S{sector}_AvgDelta"] = valid.mean() if not valid.empty else None

        result_rows.append(row)

    return pd.DataFrame(result_rows)


def get_sector_comparison_summary(
    driver1_laps: pd.DataFrame, driver2_laps: pd.DataFrame
) -> pd.DataFrame:
    """
    Get a summary table comparing sector performance between drivers.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver

    Returns:
        DataFrame with sector comparison summary
    """
    if driver1_laps.empty or driver2_laps.empty:
        return pd.DataFrame()

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    summary1 = get_sector_summary(driver1_laps)
    summary2 = get_sector_summary(driver2_laps)

    if not summary1 or not summary2:
        return pd.DataFrame()

    rows = []
    for s1, s2 in zip(summary1, summary2):
        delta_best = s1.best_time - s2.best_time
        delta_avg = s1.avg_time - s2.avg_time

        rows.append(
            {
                "Sector": f"S{s1.sector}",
                f"{driver1} Best": f"{s1.best_time:.3f}s",
                f"{driver2} Best": f"{s2.best_time:.3f}s",
                "Best Delta": f"{delta_best:+.3f}s",
                f"{driver1} Avg": f"{s1.avg_time:.3f}s",
                f"{driver2} Avg": f"{s2.avg_time:.3f}s",
                "Avg Delta": f"{delta_avg:+.3f}s",
            }
        )

    return pd.DataFrame(rows)

