"""Enhanced insights generation for race analysis."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import numpy as np
import pandas as pd

from analysis.strategy import calculate_stints, get_pit_stops

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of race insights."""

    STRATEGY = "strategy"
    DEGRADATION = "degradation"
    PACE = "pace"
    COMPARISON = "comparison"


@dataclass
class Insight:
    """Represents a race insight."""

    insight_type: InsightType
    message: str
    importance: int  # 1-3, higher is more important
    icon: str


def generate_race_insights(
    laps_df: pd.DataFrame,
    comparison_laps: Optional[pd.DataFrame] = None,
) -> List[Insight]:
    """
    Generate comprehensive race insights for a driver.

    Args:
        laps_df: Laps DataFrame for the main driver
        comparison_laps: Optional laps for comparison driver

    Returns:
        List of Insight objects sorted by importance
    """
    if laps_df.empty:
        return []

    insights: List[Insight] = []

    driver = laps_df.iloc[0]["Driver"] if "Driver" in laps_df.columns else "Driver"

    # Strategy insights
    insights.extend(_generate_strategy_insights(driver, laps_df))

    # Degradation insights
    insights.extend(_generate_degradation_insights(driver, laps_df))

    # Pace insights
    insights.extend(_generate_pace_insights(driver, laps_df))

    # Comparison insights (if second driver provided)
    if comparison_laps is not None and not comparison_laps.empty:
        insights.extend(_generate_comparison_insights(laps_df, comparison_laps))

    # Sort by importance (highest first)
    insights.sort(key=lambda x: x.importance, reverse=True)

    return insights


def _generate_strategy_insights(driver: str, laps_df: pd.DataFrame) -> List[Insight]:
    """Generate strategy-related insights."""
    insights = []

    stints = calculate_stints(laps_df)
    pit_stops = get_pit_stops(laps_df)

    if not stints:
        return insights

    # Number of pit stops insight
    num_stops = len(pit_stops)
    if num_stops == 0:
        insights.append(
            Insight(
                insight_type=InsightType.STRATEGY,
                message=f"{driver} completed the race without pitting (one-stop strategy or no stops)",
                importance=2,
                icon="🔧",
            )
        )
    elif num_stops >= 3:
        insights.append(
            Insight(
                insight_type=InsightType.STRATEGY,
                message=f"{driver} made {num_stops} pit stops - an aggressive multi-stop strategy",
                importance=2,
                icon="🔧",
            )
        )

    # Analyze stint lengths
    if len(stints) >= 2:
        longest_stint = max(stints, key=lambda s: s.laps_completed)

        if longest_stint.laps_completed >= 25:
            insights.append(
                Insight(
                    insight_type=InsightType.STRATEGY,
                    message=(
                        f"{driver}'s longest stint was {longest_stint.laps_completed} laps "
                        f"on {longest_stint.compound} (Laps {longest_stint.lap_start}-{longest_stint.lap_end})"
                    ),
                    importance=1,
                    icon="📊",
                )
            )

    # Undercut/overcut detection based on position changes
    undercut_result = detect_undercut_attempts(laps_df)
    if undercut_result:
        insights.append(undercut_result)

    return insights


def _generate_degradation_insights(driver: str, laps_df: pd.DataFrame) -> List[Insight]:
    """Generate degradation-related insights."""
    insights = []

    stints = calculate_stints(laps_df)

    for stint in stints:
        # Get laps for this stint
        stint_laps = laps_df[
            (laps_df["LapNumber"] >= stint.lap_start)
            & (laps_df["LapNumber"] <= stint.lap_end)
        ]

        if len(stint_laps) < 5:
            continue

        # Check for tire cliff
        cliff_insight = detect_tire_cliff(driver, stint_laps, stint.compound)
        if cliff_insight:
            insights.append(cliff_insight)

        # Check degradation rate
        lap_times = stint_laps[stint_laps["LapTime"].notna()]["LapTime"]
        if len(lap_times) >= 5:
            times_seconds = lap_times.apply(lambda x: x.total_seconds()).values
            lap_numbers = np.arange(len(times_seconds))
            # Simple linear regression to get slope (degradation rate)
            coefficients = np.polyfit(lap_numbers, times_seconds, 1)
            deg_rate = coefficients[0]  # slope = degradation rate

            if deg_rate > 0.15:  # More than 0.15s/lap degradation
                insights.append(
                    Insight(
                        insight_type=InsightType.DEGRADATION,
                        message=(
                            f"{driver} experienced high degradation on {stint.compound}: "
                            f"{deg_rate:.2f}s/lap (Stint {stint.stint_number})"
                        ),
                        importance=2,
                        icon="📉",
                    )
                )
            elif deg_rate < 0.05 and stint.laps_completed >= 10:
                insights.append(
                    Insight(
                        insight_type=InsightType.DEGRADATION,
                        message=(
                            f"{driver} showed excellent tire management on {stint.compound}: "
                            f"only {deg_rate:.2f}s/lap degradation over {stint.laps_completed} laps"
                        ),
                        importance=2,
                        icon="✨",
                    )
                )

    return insights


def _generate_pace_insights(driver: str, laps_df: pd.DataFrame) -> List[Insight]:
    """Generate pace-related insights."""
    insights = []

    valid_laps = laps_df[
        (laps_df["LapTime"].notna())
        & (laps_df["PitInTime"].isna())
        & (laps_df["PitOutTime"].isna())
    ]

    if valid_laps.empty:
        return insights

    lap_times = valid_laps["LapTime"].apply(lambda x: x.total_seconds())

    # Fastest lap info
    fastest_idx = lap_times.idxmin()
    fastest_lap = valid_laps.loc[fastest_idx]
    fastest_time = lap_times.min()
    fastest_lap_num = fastest_lap["LapNumber"]
    compound = fastest_lap.get("Compound", "Unknown")

    insights.append(
        Insight(
            insight_type=InsightType.PACE,
            message=(
                f"{driver}'s fastest lap was {fastest_time:.3f}s on lap {int(fastest_lap_num)} "
                f"({compound})"
            ),
            importance=1,
            icon="⚡",
        )
    )

    # Consistency analysis
    std_dev = lap_times.std()
    if std_dev < 0.5:
        insights.append(
            Insight(
                insight_type=InsightType.PACE,
                message=(
                    f"{driver} showed excellent consistency with only {std_dev:.3f}s "
                    f"standard deviation across clean laps"
                ),
                importance=2,
                icon="🎯",
            )
        )
    elif std_dev > 1.5:
        insights.append(
            Insight(
                insight_type=InsightType.PACE,
                message=(
                    f"{driver} had variable pace with {std_dev:.3f}s standard deviation "
                    f"(possible traffic or tire issues)"
                ),
                importance=1,
                icon="📈",
            )
        )

    return insights


def _generate_comparison_insights(
    driver1_laps: pd.DataFrame,
    driver2_laps: pd.DataFrame,
) -> List[Insight]:
    """Generate comparison insights between two drivers."""
    insights = []

    if driver1_laps.empty or driver2_laps.empty:
        return insights

    driver1 = driver1_laps.iloc[0]["Driver"]
    driver2 = driver2_laps.iloc[0]["Driver"]

    # Find common laps
    common_laps = set(driver1_laps["LapNumber"]) & set(driver2_laps["LapNumber"])

    if not common_laps:
        return insights

    # Count laps won
    driver1_faster = 0
    driver2_faster = 0
    total_delta = 0.0

    for lap_num in common_laps:
        lap1 = driver1_laps[driver1_laps["LapNumber"] == lap_num].iloc[0]
        lap2 = driver2_laps[driver2_laps["LapNumber"] == lap_num].iloc[0]

        if pd.isna(lap1.get("LapTime")) or pd.isna(lap2.get("LapTime")):
            continue

        t1 = lap1["LapTime"].total_seconds()
        t2 = lap2["LapTime"].total_seconds()
        delta = t1 - t2

        total_delta += delta

        if t1 < t2:
            driver1_faster += 1
        elif t2 < t1:
            driver2_faster += 1

    total_compared = driver1_faster + driver2_faster

    if total_compared > 0:
        insights.append(
            Insight(
                insight_type=InsightType.COMPARISON,
                message=(
                    f"{driver1} won {driver1_faster} of {total_compared} comparable laps "
                    f"vs {driver2} ({driver2_faster} laps)"
                ),
                importance=3,
                icon="⚔️",
            )
        )

        avg_delta = total_delta / total_compared
        if abs(avg_delta) >= 0.1:
            faster = driver1 if avg_delta < 0 else driver2
            insights.append(
                Insight(
                    insight_type=InsightType.COMPARISON,
                    message=f"{faster} was {abs(avg_delta):.3f}s faster on average per lap",
                    importance=2,
                    icon="🏎️",
                )
            )

    return insights


def detect_undercut_attempts(laps_df: pd.DataFrame) -> Optional[Insight]:
    """
    Detect if driver gained or lost positions through pit strategy.

    Args:
        laps_df: Laps DataFrame for the driver

    Returns:
        Insight if undercut/overcut detected, None otherwise
    """
    if laps_df.empty or "Position" not in laps_df.columns:
        return None

    stints = calculate_stints(laps_df)

    if len(stints) < 2:
        return None

    driver = laps_df.iloc[0]["Driver"]

    for i in range(len(stints) - 1):
        current_stint = stints[i]
        next_stint = stints[i + 1]

        if current_stint.position_end is None or next_stint.position_start is None:
            continue

        # Position at end of current stint vs start of next stint
        # (position gained/lost during pit window)
        pos_before = current_stint.position_end
        pos_after = next_stint.position_start

        if pos_after is not None and pos_before is not None:
            pos_change = pos_before - pos_after

            if pos_change >= 2:
                return Insight(
                    insight_type=InsightType.STRATEGY,
                    message=(
                        f"{driver} gained {pos_change} positions through pit stop "
                        f"at lap {current_stint.lap_end} (undercut/timing advantage)"
                    ),
                    importance=3,
                    icon="🚀",
                )
            elif pos_change <= -2:
                return Insight(
                    insight_type=InsightType.STRATEGY,
                    message=(
                        f"{driver} lost {abs(pos_change)} positions through pit stop "
                        f"at lap {current_stint.lap_end} (overcut by rivals)"
                    ),
                    importance=2,
                    icon="⚠️",
                )

    return None


def detect_tire_cliff(
    driver: str,
    stint_laps: pd.DataFrame,
    compound: str,
) -> Optional[Insight]:
    """
    Detect sudden tire performance drop-off (cliff).

    Args:
        driver: Driver name
        stint_laps: Laps for a single stint
        compound: Tire compound

    Returns:
        Insight if cliff detected, None otherwise
    """
    if stint_laps.empty or len(stint_laps) < 5:
        return None

    valid_laps = stint_laps[
        (stint_laps["LapTime"].notna())
        & (stint_laps["PitInTime"].isna())
        & (stint_laps["PitOutTime"].isna())
    ]

    if len(valid_laps) < 5:
        return None

    lap_times = valid_laps["LapTime"].apply(lambda x: x.total_seconds())
    lap_numbers = valid_laps["LapNumber"]

    # Calculate lap-to-lap deltas
    deltas = lap_times.diff()

    # Look for sudden jumps (> 1.5s slower than previous lap)
    cliff_threshold = 1.5

    for i in range(1, len(deltas)):
        if pd.notna(deltas.iloc[i]) and deltas.iloc[i] > cliff_threshold:
            # Check if subsequent laps are also slower (not just traffic)
            if i + 2 < len(lap_times):
                subsequent_avg = lap_times.iloc[i : i + 3].mean()
                prior_avg = lap_times.iloc[max(0, i - 3) : i].mean()

                if subsequent_avg > prior_avg + 0.5:
                    cliff_lap = int(lap_numbers.iloc[i])
                    time_lost = subsequent_avg - prior_avg

                    return Insight(
                        insight_type=InsightType.DEGRADATION,
                        message=(
                            f"{driver} experienced tire cliff on lap {cliff_lap} ({compound}) - "
                            f"lost ~{time_lost:.1f}s pace"
                        ),
                        importance=3,
                        icon="⚡",
                    )

    return None


def format_insights_for_display(insights: List[Insight]) -> dict:
    """
    Format insights for UI display, grouped by type.

    Args:
        insights: List of Insight objects

    Returns:
        Dictionary with insights grouped by type
    """
    grouped = {
        InsightType.STRATEGY: [],
        InsightType.DEGRADATION: [],
        InsightType.PACE: [],
        InsightType.COMPARISON: [],
    }

    for insight in insights:
        grouped[insight.insight_type].append(insight)

    return {
        "strategy": [(i.icon, i.message) for i in grouped[InsightType.STRATEGY]],
        "degradation": [(i.icon, i.message) for i in grouped[InsightType.DEGRADATION]],
        "pace": [(i.icon, i.message) for i in grouped[InsightType.PACE]],
        "comparison": [(i.icon, i.message) for i in grouped[InsightType.COMPARISON]],
    }

