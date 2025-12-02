"""Tire strategy timeline visualization."""

import logging
from typing import List

import pandas as pd
import plotly.graph_objects as go

from analysis.strategy import calculate_stints, get_pit_stops
from utils.colors import get_tire_color

logger = logging.getLogger(__name__)


def create_tire_timeline(
    driver_laps_list: List[tuple[str, pd.DataFrame]],
    race_distance: int,
    height: int = 400,
) -> go.Figure:
    """
    Create tire strategy timeline visualization.

    Shows horizontal bars for each stint colored by compound, with pit stop markers.

    Args:
        driver_laps_list: List of (driver_name, laps_dataframe) tuples
        race_distance: Total number of laps in the race
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    y_labels = []

    for driver, laps_df in driver_laps_list:
        if laps_df.empty:
            continue

        # Calculate stints
        stints = calculate_stints(laps_df)

        # Get pit stops
        pit_stops = get_pit_stops(laps_df)

        # Add stint bars
        for stint in stints:
            fig.add_trace(
                go.Bar(
                    x=[stint.laps_completed],
                    y=[driver],
                    orientation="h",
                    name=f"{stint.compound}",
                    marker=dict(
                        color=get_tire_color(stint.compound),
                        line=dict(color="black", width=1),
                    ),
                    base=stint.lap_start - 1,
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        f"Compound: {stint.compound}<br>"
                        f"Laps: {stint.lap_start}-{stint.lap_end} ({stint.laps_completed} laps)<br>"
                        f"Tire Age: {stint.tire_age_at_start} laps<br>"
                        f"Avg Lap: {stint.avg_lap_time:.3f}s<br>"
                        "<extra></extra>"
                    )
                    if stint.avg_lap_time
                    else (
                        f"<b>{driver}</b><br>"
                        f"Compound: {stint.compound}<br>"
                        f"Laps: {stint.lap_start}-{stint.lap_end} ({stint.laps_completed} laps)<br>"
                        f"Tire Age: {stint.tire_age_at_start} laps<br>"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                )
            )

        # Add pit stop markers using driver name for correct y-positioning
        for _, pit_stop in pit_stops.iterrows():
            lap_num = pit_stop["LapNumber"]
            duration = pit_stop["Duration"]

            # Add pit stop annotation with marker
            annotation_text = f"🔧 {duration:.1f}s" if pd.notna(duration) else "🔧"
            fig.add_annotation(
                x=lap_num,
                y=driver,  # Use driver name for categorical y-axis
                text=annotation_text,
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="red",
                ax=0,
                ay=-30,
                font=dict(size=10, color="red"),
                bgcolor="white",
                bordercolor="red",
                borderwidth=1,
                borderpad=2,
            )

        y_labels.append(driver)

    # Update layout
    fig.update_layout(
        title="Tire Strategy Timeline",
        xaxis_title="Lap Number",
        yaxis_title="Driver",
        xaxis=dict(
            range=[0, race_distance + 1],
            dtick=5,
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(
            categoryorder="array",
            categoryarray=y_labels[::-1],  # Reverse to show first driver on top
        ),
        height=height,
        hovermode="closest",
        plot_bgcolor="white",
        showlegend=False,
        bargap=0.3,
    )

    # Add legend manually for tire compounds
    unique_compounds = set()
    for driver, laps_df in driver_laps_list:
        if not laps_df.empty and "Compound" in laps_df.columns:
            unique_compounds.update(laps_df["Compound"].dropna().unique())

    # Add invisible traces for legend
    for compound in sorted(unique_compounds):
        if compound and compound != "UNKNOWN":
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(
                        size=15,
                        color=get_tire_color(compound),
                        line=dict(color="black", width=1),
                    ),
                    name=compound,
                    showlegend=True,
                )
            )

    return fig


def create_simple_stint_table(driver: str, laps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a simple table showing stint information.

    Args:
        driver: Driver name
        laps_df: Laps DataFrame for the driver

    Returns:
        DataFrame with stint summary
    """
    stints = calculate_stints(laps_df)

    if not stints:
        return pd.DataFrame()

    stint_data = []
    for stint in stints:
        stint_data.append(
            {
                "Stint": stint.stint_number,
                "Compound": stint.compound,
                "Laps": f"{stint.lap_start}-{stint.lap_end}",
                "Count": stint.laps_completed,
                "Avg Time": f"{stint.avg_lap_time:.3f}s" if stint.avg_lap_time else "N/A",
                "Position": f"P{stint.position_start} → P{stint.position_end}"
                if stint.position_start and stint.position_end
                else "N/A",
            }
        )

    return pd.DataFrame(stint_data)

