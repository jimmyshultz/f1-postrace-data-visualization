"""Sector time comparison visualizations."""

import logging

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.sectors import get_sector_comparison, get_sector_times
from utils.colors import get_team_color

logger = logging.getLogger(__name__)


def create_sector_delta_chart(
    driver1_laps: pd.DataFrame,
    driver2_laps: pd.DataFrame,
    height: int = 400,
) -> go.Figure:
    """
    Create stacked bar chart showing sector time deltas per lap.

    Positive values = driver2 faster, Negative = driver1 faster.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    comparison = get_sector_comparison(driver1_laps, driver2_laps)

    if comparison.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient sector data for comparison",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(height=height)
        return fig

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    fig = go.Figure()

    # Add bar for each sector
    sector_colors = {
        1: "#FF6B6B",  # Red-ish for S1
        2: "#4ECDC4",  # Teal for S2
        3: "#45B7D1",  # Blue for S3
    }

    for sector in [1, 2, 3]:
        delta_col = f"S{sector}_Delta"
        valid_data = comparison[comparison[delta_col].notna()]

        if valid_data.empty:
            continue

        fig.add_trace(
            go.Bar(
                x=valid_data["LapNumber"],
                y=valid_data[delta_col],
                name=f"Sector {sector}",
                marker_color=sector_colors[sector],
                hovertemplate=(
                    f"<b>Lap %{{x}}</b><br>"
                    f"Sector {sector} Delta: %{{y:.3f}}s<br>"
                    f"<i>Negative = {driver1} faster</i><br>"
                    "<extra></extra>"
                ),
            )
        )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add annotations for driver advantage
    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"↓ {driver1} faster",
        showarrow=False,
        font=dict(size=10, color="green"),
    )
    fig.add_annotation(
        x=0.02,
        y=0.02,
        xref="paper",
        yref="paper",
        text=f"↑ {driver2} faster",
        showarrow=False,
        font=dict(size=10, color="red"),
    )

    fig.update_layout(
        title=f"Sector Time Comparison: {driver1} vs {driver2}",
        xaxis_title="Lap Number",
        yaxis_title="Delta (seconds)",
        barmode="relative",
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
        xaxis=dict(showgrid=True, gridcolor="lightgray"),
        yaxis=dict(showgrid=True, gridcolor="lightgray"),
    )

    return fig


def create_sector_scatter(
    driver1_laps: pd.DataFrame,
    driver2_laps: pd.DataFrame,
    height: int = 500,
) -> go.Figure:
    """
    Create scatter plot comparing sector times between drivers.

    Each subplot shows one sector with both drivers' times.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    sector_times_1 = get_sector_times(driver1_laps)
    sector_times_2 = get_sector_times(driver2_laps)

    if sector_times_1.empty or sector_times_2.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient sector data for comparison",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(height=height)
        return fig

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    # Get team colors
    team1 = driver1_laps.iloc[0].get("Team") if not driver1_laps.empty else None
    team2 = driver2_laps.iloc[0].get("Team") if not driver2_laps.empty else None
    color1 = get_team_color(team1) if team1 else "#3671C6"
    color2 = get_team_color(team2) if team2 else "#E8002D"

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Sector 1", "Sector 2", "Sector 3"),
        horizontal_spacing=0.08,
    )

    for sector in [1, 2, 3]:
        col_name = f"Sector{sector}"

        # Driver 1
        valid_1 = sector_times_1[sector_times_1[col_name].notna()]
        if not valid_1.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_1["LapNumber"],
                    y=valid_1[col_name],
                    mode="markers+lines",
                    name=driver1 if sector == 1 else None,
                    showlegend=(sector == 1),
                    line=dict(color=color1, width=2),
                    marker=dict(size=4, color=color1),
                    hovertemplate=(
                        f"<b>{driver1}</b><br>"
                        f"Lap: %{{x}}<br>"
                        f"S{sector}: %{{y:.3f}}s<br>"
                        "<extra></extra>"
                    ),
                    legendgroup=driver1,
                ),
                row=1,
                col=sector,
            )

        # Driver 2
        valid_2 = sector_times_2[sector_times_2[col_name].notna()]
        if not valid_2.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_2["LapNumber"],
                    y=valid_2[col_name],
                    mode="markers+lines",
                    name=driver2 if sector == 1 else None,
                    showlegend=(sector == 1),
                    line=dict(color=color2, width=2),
                    marker=dict(size=4, color=color2),
                    hovertemplate=(
                        f"<b>{driver2}</b><br>"
                        f"Lap: %{{x}}<br>"
                        f"S{sector}: %{{y:.3f}}s<br>"
                        "<extra></extra>"
                    ),
                    legendgroup=driver2,
                ),
                row=1,
                col=sector,
            )

    fig.update_layout(
        title=f"Sector Times: {driver1} vs {driver2}",
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

    # Update axes for all subplots
    for i in range(1, 4):
        fig.update_xaxes(title_text="Lap", showgrid=True, gridcolor="lightgray", row=1, col=i)
        fig.update_yaxes(title_text="Time (s)", showgrid=True, gridcolor="lightgray", row=1, col=i)

    return fig


def create_sector_advantage_chart(
    driver1_laps: pd.DataFrame,
    driver2_laps: pd.DataFrame,
    height: int = 300,
) -> go.Figure:
    """
    Create horizontal bar chart showing which driver has advantage in each sector.

    Args:
        driver1_laps: Laps for first driver
        driver2_laps: Laps for second driver
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    comparison = get_sector_comparison(driver1_laps, driver2_laps)

    if comparison.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for sector advantage analysis",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        fig.update_layout(height=height)
        return fig

    driver1 = driver1_laps.iloc[0]["Driver"] if not driver1_laps.empty else "Driver1"
    driver2 = driver2_laps.iloc[0]["Driver"] if not driver2_laps.empty else "Driver2"

    # Get team colors
    team1 = driver1_laps.iloc[0].get("Team") if not driver1_laps.empty else None
    team2 = driver2_laps.iloc[0].get("Team") if not driver2_laps.empty else None
    color1 = get_team_color(team1) if team1 else "#3671C6"
    color2 = get_team_color(team2) if team2 else "#E8002D"

    # Calculate average deltas per sector
    sectors = ["S1", "S2", "S3"]
    avg_deltas = []

    for sector in [1, 2, 3]:
        delta_col = f"S{sector}_Delta"
        valid = comparison[comparison[delta_col].notna()][delta_col]
        avg_deltas.append(valid.mean() if not valid.empty else 0)

    fig = go.Figure()

    # Create bars - negative (driver1 faster) on left, positive (driver2 faster) on right
    for i, (sector, delta) in enumerate(zip(sectors, avg_deltas)):
        color = color1 if delta < 0 else color2
        driver = driver1 if delta < 0 else driver2

        fig.add_trace(
            go.Bar(
                y=[sector],
                x=[delta],
                orientation="h",
                marker_color=color,
                name=driver,
                showlegend=False,
                hovertemplate=(
                    f"<b>{sector}</b><br>"
                    f"Avg Delta: {delta:+.3f}s<br>"
                    f"<i>{driver} faster</i><br>"
                    "<extra></extra>"
                ),
            )
        )

    # Add zero line
    fig.add_vline(x=0, line_dash="dash", line_color="gray")

    # Add driver labels
    fig.add_annotation(
        x=-0.15,
        y=1.1,
        xref="paper",
        yref="paper",
        text=f"← {driver1} faster",
        showarrow=False,
        font=dict(color=color1, size=11),
    )
    fig.add_annotation(
        x=0.85,
        y=1.1,
        xref="paper",
        yref="paper",
        text=f"{driver2} faster →",
        showarrow=False,
        font=dict(color=color2, size=11),
    )

    fig.update_layout(
        title="Sector Advantage (Avg Delta)",
        xaxis_title="Delta (seconds)",
        height=height,
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            zeroline=True,
        ),
        yaxis=dict(showgrid=False),
    )

    return fig

