"""Lap time degradation visualization."""

import logging
from typing import List

import pandas as pd
import plotly.graph_objects as go

from analysis.degradation import filter_clean_laps_for_chart
from data.preprocessor import get_driver_stint_data
from utils.colors import get_tire_color

logger = logging.getLogger(__name__)


def create_degradation_chart(
    driver_laps_list: List[tuple[str, pd.DataFrame, str]],
    height: int = 600,
) -> go.Figure:
    """
    Create lap time degradation visualization.

    Shows lap times over the race with different colors for tire compounds.

    Args:
        driver_laps_list: List of (driver_name, laps_df, team_color) tuples
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    for driver, laps_df, team_color in driver_laps_list:
        if laps_df.empty:
            continue

        # Add stint information
        stint_laps = get_driver_stint_data(laps_df)

        if stint_laps.empty:
            continue

        # Filter to clean laps for better visualization
        clean_laps = filter_clean_laps_for_chart(stint_laps)

        if clean_laps.empty:
            continue

        # Plot each stint separately for different colors
        stint_numbers = clean_laps["StintNumber"].unique()

        for stint_num in stint_numbers:
            stint_data = clean_laps[clean_laps["StintNumber"] == stint_num]

            if stint_data.empty:
                continue

            compound = stint_data.iloc[0]["Compound"]
            lap_numbers = stint_data["LapNumber"].values
            lap_times = stint_data["LapTime"].apply(lambda x: x.total_seconds()).values

            # Determine line style based on compound
            line_style = get_line_style_for_compound(compound)

            fig.add_trace(
                go.Scatter(
                    x=lap_numbers,
                    y=lap_times,
                    mode="lines+markers",
                    name=f"{driver} - {compound}",
                    line=dict(
                        color=team_color if team_color else get_tire_color(compound),
                        width=2,
                        dash=line_style,
                    ),
                    marker=dict(size=4, color=get_tire_color(compound)),
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        "Lap: %{x}<br>"
                        "Time: %{y:.3f}s<br>"
                        f"Compound: {compound}<br>"
                        "<extra></extra>"
                    ),
                )
            )

        # Add pit stop markers
        pit_laps = laps_df[laps_df["PitInTime"].notna()]
        for _, pit_lap in pit_laps.iterrows():
            lap_num = pit_lap["LapNumber"]

            # Add vertical line
            fig.add_vline(
                x=lap_num,
                line_dash="dot",
                line_color="red",
                opacity=0.5,
                annotation_text=f"Pit (L{lap_num})",
                annotation_position="top",
            )

    # Update layout
    fig.update_layout(
        title="Lap Time Degradation Analysis",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
        ),
        height=height,
        hovermode="x unified",
        plot_bgcolor="white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
        ),
    )

    return fig


def get_line_style_for_compound(compound: str) -> str:
    """
    Get line style for a tire compound.

    Args:
        compound: Tire compound name

    Returns:
        Plotly line dash style
    """
    compound_styles = {
        "SOFT": "solid",
        "MEDIUM": "dash",
        "HARD": "dot",
        "INTERMEDIATE": "dashdot",
        "WET": "dashdot",
    }

    return compound_styles.get(compound.upper(), "solid")


def create_degradation_comparison(
    driver_1: str,
    driver_1_laps: pd.DataFrame,
    driver_2: str,
    driver_2_laps: pd.DataFrame,
    height: int = 600,
) -> go.Figure:
    """
    Create side-by-side degradation comparison.

    Args:
        driver_1: First driver name
        driver_1_laps: First driver laps
        driver_2: Second driver name
        driver_2_laps: Second driver laps
        height: Chart height

    Returns:
        Plotly Figure with subplots
    """
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(driver_1, driver_2),
        shared_yaxes=True,
    )

    # Process both drivers
    for idx, (driver, laps_df) in enumerate(
        [(driver_1, driver_1_laps), (driver_2, driver_2_laps)], start=1
    ):
        stint_laps = get_driver_stint_data(laps_df)
        clean_laps = filter_clean_laps_for_chart(stint_laps)

        if clean_laps.empty:
            continue

        stint_numbers = clean_laps["StintNumber"].unique()

        for stint_num in stint_numbers:
            stint_data = clean_laps[clean_laps["StintNumber"] == stint_num]
            compound = stint_data.iloc[0]["Compound"]
            lap_numbers = stint_data["LapNumber"].values
            lap_times = stint_data["LapTime"].apply(lambda x: x.total_seconds()).values

            fig.add_trace(
                go.Scatter(
                    x=lap_numbers,
                    y=lap_times,
                    mode="lines+markers",
                    name=compound,
                    line=dict(color=get_tire_color(compound), width=2),
                    marker=dict(size=4),
                    showlegend=(idx == 1),  # Only show legend once
                ),
                row=1,
                col=idx,
            )

    fig.update_xaxes(title_text="Lap Number", row=1, col=1)
    fig.update_xaxes(title_text="Lap Number", row=1, col=2)
    fig.update_yaxes(title_text="Lap Time (seconds)", row=1, col=1)

    fig.update_layout(
        height=height,
        hovermode="x unified",
        plot_bgcolor="white",
    )

    return fig

