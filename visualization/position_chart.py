"""Position changes (bumps chart) visualization."""

import logging
from typing import List, Optional

import pandas as pd
import plotly.graph_objects as go

from utils.colors import get_team_color

logger = logging.getLogger(__name__)


def create_position_chart(
    driver_laps_list: List[tuple[str, pd.DataFrame, Optional[str]]],
    race_distance: int,
    height: int = 500,
    show_all_drivers: bool = False,
    all_drivers_laps: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """
    Create position changes visualization (bumps chart).

    Shows driver positions lap-by-lap throughout the race.

    Args:
        driver_laps_list: List of (driver_name, laps_df, team_color) tuples for main drivers
        race_distance: Total number of laps in the race
        height: Chart height in pixels
        show_all_drivers: Whether to show all drivers as faded background lines
        all_drivers_laps: Full laps DataFrame for all drivers (if show_all_drivers)

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Add faded background lines for all drivers if requested
    if show_all_drivers and all_drivers_laps is not None:
        selected_drivers = [d[0] for d in driver_laps_list]
        all_driver_names = all_drivers_laps["Driver"].unique()

        for driver in all_driver_names:
            if driver in selected_drivers:
                continue  # Skip selected drivers, they'll be drawn later

            driver_laps = all_drivers_laps[all_drivers_laps["Driver"] == driver]
            if driver_laps.empty:
                continue

            lap_numbers, positions = _extract_position_data(driver_laps)
            if not lap_numbers:
                continue

            # Get team color
            team = driver_laps.iloc[0].get("Team")
            team_color = get_team_color(team) if team else "#808080"

            fig.add_trace(
                go.Scatter(
                    x=lap_numbers,
                    y=positions,
                    mode="lines",
                    name=driver,
                    line=dict(
                        color=team_color,
                        width=1,
                    ),
                    opacity=0.2,
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        "Lap: %{x}<br>"
                        "Position: P%{y}<br>"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

    # Add main driver traces
    for driver, laps_df, team_color in driver_laps_list:
        if laps_df.empty:
            continue

        lap_numbers, positions = _extract_position_data(laps_df)
        if not lap_numbers:
            continue

        # Use provided team color or extract from data
        if not team_color:
            team = laps_df.iloc[0].get("Team")
            team_color = get_team_color(team) if team else "#808080"

        # Add position line
        fig.add_trace(
            go.Scatter(
                x=lap_numbers,
                y=positions,
                mode="lines+markers",
                name=driver,
                line=dict(
                    color=team_color,
                    width=3,
                ),
                marker=dict(
                    size=4,
                    color=team_color,
                ),
                hovertemplate=(
                    f"<b>{driver}</b><br>"
                    "Lap: %{x}<br>"
                    "Position: P%{y}<br>"
                    "<extra></extra>"
                ),
            )
        )

        # Add pit stop markers
        _add_pit_stop_markers(fig, driver, laps_df, team_color)

    # Update layout
    fig.update_layout(
        title="Position Changes Throughout Race",
        xaxis_title="Lap Number",
        yaxis_title="Position",
        xaxis=dict(
            range=[0, race_distance + 1],
            dtick=5,
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            range=[21, 0],  # Inverted: P1 at top
            dtick=1,
            showgrid=True,
            gridcolor="lightgray",
            tickmode="linear",
        ),
        height=height,
        hovermode="x unified",
        plot_bgcolor="white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    return fig


def _extract_position_data(laps_df: pd.DataFrame) -> tuple[List[int], List[int]]:
    """
    Extract lap numbers and positions from laps DataFrame.

    Args:
        laps_df: DataFrame with lap data

    Returns:
        Tuple of (lap_numbers, positions) lists
    """
    if laps_df.empty or "Position" not in laps_df.columns:
        return [], []

    # Filter to laps with valid position data
    valid_laps = laps_df[laps_df["Position"].notna()].copy()

    if valid_laps.empty:
        return [], []

    # Sort by lap number
    valid_laps = valid_laps.sort_values("LapNumber")

    lap_numbers = valid_laps["LapNumber"].astype(int).tolist()
    positions = valid_laps["Position"].astype(int).tolist()

    return lap_numbers, positions


def _add_pit_stop_markers(
    fig: go.Figure,
    driver: str,
    laps_df: pd.DataFrame,
    team_color: str,
) -> None:
    """
    Add pit stop markers to the position chart.

    Args:
        fig: Plotly figure to add markers to
        driver: Driver name
        laps_df: Laps DataFrame
        team_color: Team color for styling
    """
    pit_laps = laps_df[laps_df["PitInTime"].notna()]

    for _, pit_lap in pit_laps.iterrows():
        lap_num = pit_lap["LapNumber"]
        position = pit_lap.get("Position")

        if pd.notna(position):
            fig.add_trace(
                go.Scatter(
                    x=[lap_num],
                    y=[position],
                    mode="markers",
                    marker=dict(
                        symbol="circle-open",
                        size=12,
                        color=team_color,
                        line=dict(width=2, color=team_color),
                    ),
                    name=f"{driver} Pit",
                    hovertemplate=(
                        f"<b>{driver} Pit Stop</b><br>"
                        f"Lap: {int(lap_num)}<br>"
                        f"Position: P{int(position)}<br>"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )


def get_position_summary(laps_df: pd.DataFrame) -> dict:
    """
    Get position summary statistics for a driver.

    Args:
        laps_df: Laps DataFrame for a driver

    Returns:
        Dictionary with position statistics
    """
    if laps_df.empty or "Position" not in laps_df.columns:
        return {
            "start_position": None,
            "end_position": None,
            "best_position": None,
            "worst_position": None,
            "positions_gained": None,
            "position_changes": 0,
        }

    valid_laps = laps_df[laps_df["Position"].notna()].copy()

    if valid_laps.empty:
        return {
            "start_position": None,
            "end_position": None,
            "best_position": None,
            "worst_position": None,
            "positions_gained": None,
            "position_changes": 0,
        }

    valid_laps = valid_laps.sort_values("LapNumber")
    positions = valid_laps["Position"].astype(int)

    start_pos = positions.iloc[0]
    end_pos = positions.iloc[-1]
    best_pos = positions.min()
    worst_pos = positions.max()
    positions_gained = start_pos - end_pos

    # Count position changes
    position_changes = (positions.diff().abs() > 0).sum()

    return {
        "start_position": int(start_pos),
        "end_position": int(end_pos),
        "best_position": int(best_pos),
        "worst_position": int(worst_pos),
        "positions_gained": int(positions_gained),
        "position_changes": int(position_changes),
    }

