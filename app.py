"""Main Streamlit application for F1 Strategy Analyzer."""

import logging
from typing import Optional

import pandas as pd
import streamlit as st

from config import settings
from data.loader import get_race_names, load_session
from data.preprocessor import validate_session_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "session_data" not in st.session_state:
        st.session_state.session_data = None
    if "selected_driver_1" not in st.session_state:
        st.session_state.selected_driver_1 = None
    if "selected_driver_2" not in st.session_state:
        st.session_state.selected_driver_2 = None
    if "comparison_mode" not in st.session_state:
        st.session_state.comparison_mode = False


def render_header() -> None:
    """Render the application header."""
    st.title(f"{settings.APP_ICON} {settings.APP_TITLE}")
    st.markdown(
        "Analyze F1 race strategies, tire degradation, and driver performance with interactive visualizations."
    )

    # Add helpful info in expander
    with st.expander("ℹ️ How to use this app"):
        st.markdown(
            "**Step 1:** Select a year, race, and session type from the dropdowns above\n\n"
            "**Step 2:** Click 'Load Session' and wait for the data to load (first time may take 30 seconds)\n\n"
            "**Step 3:** Choose a driver to analyze from the dropdown\n\n"
            "**Step 4:** Optionally enable 'Compare' mode to analyze two drivers side-by-side\n\n"
            "**Step 5:** Explore the visualizations and statistics below\n\n"
            "**Tips:**\n"
            "- Hover over charts for detailed information\n"
            "- Zoom and pan on charts for closer inspection\n"
            "- All data is cached locally for faster subsequent loads"
        )

    st.divider()


def render_session_selection() -> None:
    """Render the session selection UI."""
    st.subheader("📅 Session Selection")

    col1, col2, col3, col4 = st.columns([2, 3, 2, 2])

    with col1:
        year = st.selectbox(
            "Year",
            options=settings.AVAILABLE_YEARS,
            index=0,
            key="year_select",
        )

    with col2:
        # Get race names for selected year
        try:
            race_names = get_race_names(year)
            if not race_names:
                st.error(f"❌ No races found for {year}. Please check your internet connection.")
                return

            race = st.selectbox(
                "Race",
                options=race_names,
                index=0,
                key="race_select",
            )
        except Exception as e:
            st.error(f"❌ Failed to fetch race schedule: {str(e)}")
            st.info("💡 Please check your internet connection and try again.")
            return

    with col3:
        session_type = st.selectbox(
            "Session",
            options=settings.SESSION_TYPES,
            index=0,
            key="session_type_select",
        )

    with col4:
        st.write("")  # Spacing
        st.write("")  # Spacing
        load_button = st.button("🏁 Load Session", type="primary", use_container_width=True)

    if load_button:
        with st.spinner(f"⏳ Loading {year} {race} - {session_type}... (This may take up to 30 seconds for uncached sessions)"):
            try:
                session_data = load_session(year, race, session_type)

                if session_data and validate_session_data(session_data):
                    st.session_state.session_data = session_data
                    st.success(
                        f"✅ Successfully loaded {race} {session_type}! "
                        f"{len(session_data.drivers)} drivers, "
                        f"{len(session_data.laps)} laps"
                    )
                    st.rerun()
                else:
                    st.error(
                        "❌ Failed to load session data or data validation failed. "
                        "This session may not have complete data available."
                    )
                    st.info(
                        "💡 Try a different session or check if the session has been completed. "
                        "Very recent sessions may not have data available yet."
                    )

            except Exception as e:
                st.error(f"❌ Error loading session: {str(e)}")
                st.info(
                    "💡 Common issues:\n"
                    "- Internet connection required for first-time loads\n"
                    "- Very recent sessions may not have data yet\n"
                    "- Session may have been cancelled or postponed"
                )
                logger.exception("Session loading error")


def render_session_info() -> None:
    """Render information about the currently loaded session."""
    if st.session_state.session_data is None:
        st.info("👆 Please select and load a session to begin analysis.")
        return

    session_data = st.session_state.session_data

    st.success(
        f"📊 **{session_data.year} {session_data.race_name} - {session_data.session_type}** | "
        f"{len(session_data.drivers)} drivers | "
        f"{session_data.race_distance} laps"
    )

    # Show driver list in an expander
    with st.expander("View Drivers"):
        drivers_text = ", ".join(sorted(session_data.drivers))
        st.write(drivers_text)


def main() -> None:
    """Main application entry point."""
    initialize_session_state()
    render_header()
    render_session_selection()

    st.divider()

    render_session_info()

    # Driver selection and analysis
    if st.session_state.session_data is not None:
        st.divider()
        render_driver_selection()
        render_analysis()


def render_driver_selection() -> None:
    """Render driver selection UI."""
    st.subheader("🏎️ Driver Selection")

    session_data = st.session_state.session_data
    drivers = sorted(session_data.drivers)

    if not drivers:
        st.error("❌ No drivers found in this session.")
        return

    col1, col2, col3 = st.columns([3, 1, 3])

    with col1:
        driver_1 = st.selectbox(
            "Primary Driver",
            options=drivers,
            index=0,
            key="driver_1_select",
            help="Select the main driver to analyze",
        )
        st.session_state.selected_driver_1 = driver_1

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        comparison_mode = st.checkbox(
            "Compare",
            value=st.session_state.comparison_mode,
            key="comparison_checkbox",
            help="Enable to compare two drivers side-by-side",
        )
        st.session_state.comparison_mode = comparison_mode

    with col3:
        if comparison_mode:
            # Filter out the first driver from options
            driver_2_options = [d for d in drivers if d != driver_1]
            if driver_2_options:
                driver_2 = st.selectbox(
                    "Comparison Driver",
                    options=driver_2_options,
                    index=0,
                    key="driver_2_select",
                    help="Select the second driver to compare against",
                )
                st.session_state.selected_driver_2 = driver_2
            else:
                st.warning("⚠️ No other drivers available for comparison")
                st.session_state.selected_driver_2 = None
        else:
            st.session_state.selected_driver_2 = None


def render_race_statistics(session_data, driver_1: str, driver_2: Optional[str] = None) -> None:
    """Render comprehensive race statistics panel."""
    from data.loader import get_driver_laps

    driver_1_laps = get_driver_laps(session_data, driver_1)

    if driver_2:
        driver_2_laps = get_driver_laps(session_data, driver_2)
        col1, col2 = st.columns(2)

        with col1:
            render_driver_statistics(driver_1, driver_1_laps)

        with col2:
            render_driver_statistics(driver_2, driver_2_laps)
    else:
        render_driver_statistics(driver_1, driver_1_laps)


def render_driver_statistics(driver: str, laps_df: pd.DataFrame) -> None:
    """Render statistics for a single driver."""
    from utils.helpers import calculate_average_laptime, format_laptime

    if laps_df.empty:
        st.warning(f"⚠️ No data available for {driver}")
        return

    st.markdown(f"### {driver}")

    # Overall metrics - Row 1
    col1, col2, col3, col4 = st.columns(4)

    # Starting position (grid position - position on lap 1)
    starting_position = laps_df.iloc[0]["Position"] if "Position" in laps_df.columns else None
    with col1:
        st.metric(
            "Grid Position",
            f"P{int(starting_position)}" if pd.notna(starting_position) else "N/A",
            help="Starting grid position",
        )

    # Final position
    final_position = laps_df.iloc[-1]["Position"] if "Position" in laps_df.columns else None
    with col2:
        # Calculate positions gained/lost
        if pd.notna(starting_position) and pd.notna(final_position):
            positions_changed = int(starting_position) - int(final_position)
            delta_text = f"+{positions_changed}" if positions_changed > 0 else str(positions_changed)
            delta_color = "normal" if positions_changed >= 0 else "inverse"
        else:
            delta_text = None
            delta_color = "off"

        st.metric(
            "Final Position",
            f"P{int(final_position)}" if pd.notna(final_position) else "N/A",
            delta=delta_text,
            delta_color=delta_color,
            help="Final classification position (delta shows positions gained/lost)",
        )

    # Total laps
    total_laps = len(laps_df)
    with col3:
        st.metric("Total Laps", total_laps, help="Total laps completed")

    # Pit stops
    num_pit_stops = laps_df["PitInTime"].notna().sum()
    with col4:
        st.metric("Pit Stops", num_pit_stops, help="Number of pit stops made")

    # Row 2 - Lap time metrics
    col1, col2, col3, col4 = st.columns(4)

    # Fastest lap
    fastest_lap = laps_df["LapTime"].min() if not laps_df.empty else None
    fastest_lap_rows = laps_df[laps_df["LapTime"] == fastest_lap] if pd.notna(fastest_lap) else pd.DataFrame()
    fastest_lap_num = fastest_lap_rows.iloc[0]["LapNumber"] if not fastest_lap_rows.empty else None
    with col1:
        st.metric(
            "Fastest Lap",
            format_laptime(fastest_lap),
            delta=f"Lap {int(fastest_lap_num)}" if fastest_lap_num else None,
            help="Fastest lap time and lap number",
        )

    # Average lap time (excluding pit laps)
    valid_laps = laps_df[(laps_df["PitInTime"].isna()) & (laps_df["PitOutTime"].isna())]
    avg_laptime = calculate_average_laptime(valid_laps["LapTime"]) if not valid_laps.empty else None
    with col2:
        st.metric(
            "Avg Lap Time",
            format_laptime(avg_laptime),
            help="Average lap time (excluding pit laps)",
        )


def render_analysis() -> None:
    """Render analysis visualizations."""
    from analysis.degradation import get_stint_degradation_summary
    from data.loader import get_driver_laps
    from utils.colors import get_team_color
    from visualization.degradation_chart import create_degradation_chart
    from visualization.position_chart import create_position_chart
    from visualization.tire_timeline import (
        create_simple_stint_table,
        create_tire_timeline,
    )

    session_data = st.session_state.session_data
    driver_1 = st.session_state.selected_driver_1
    driver_2 = st.session_state.selected_driver_2

    if not driver_1:
        st.info("Please select a driver to analyze.")
        return

    st.divider()

    # Race Statistics Panel
    st.subheader("📊 Race Statistics")
    render_race_statistics(session_data, driver_1, driver_2 if st.session_state.comparison_mode else None)

    st.divider()

    # Get driver laps for insights preview (needed before full laps retrieval)
    from data.loader import get_driver_laps as get_laps_for_insights

    driver_1_laps_preview = get_laps_for_insights(session_data, driver_1)
    driver_2_laps_preview = None
    if driver_2 and st.session_state.comparison_mode:
        driver_2_laps_preview = get_laps_for_insights(session_data, driver_2)

    # Key Insights Panel
    render_key_insights(driver_1, driver_1_laps_preview, driver_2, driver_2_laps_preview)

    st.divider()

    # Get driver laps
    driver_1_laps = get_driver_laps(session_data, driver_1)

    # Get team color for driver - use Team column to lookup color
    driver_1_team = driver_1_laps.iloc[0]["Team"] if not driver_1_laps.empty and "Team" in driver_1_laps.columns else None
    driver_1_team_color = get_team_color(driver_1_team) if driver_1_team else None

    drivers_to_analyze = [(driver_1, driver_1_laps)]
    drivers_for_degradation = [(driver_1, driver_1_laps, driver_1_team_color)]

    if driver_2 and st.session_state.comparison_mode:
        driver_2_laps = get_driver_laps(session_data, driver_2)
        driver_2_team = driver_2_laps.iloc[0]["Team"] if not driver_2_laps.empty and "Team" in driver_2_laps.columns else None
        driver_2_team_color = get_team_color(driver_2_team) if driver_2_team else None
        drivers_to_analyze.append((driver_2, driver_2_laps))
        drivers_for_degradation.append((driver_2, driver_2_laps, driver_2_team_color))

    # Position Changes Chart (Bumps Chart)
    st.subheader("📈 Position Changes")

    # Option to show all drivers as background
    show_all = st.checkbox(
        "Show all drivers in background",
        value=False,
        key="show_all_drivers_position",
        help="Display faded lines for all drivers to see the full race context",
    )

    position_fig = create_position_chart(
        drivers_for_degradation,  # Uses same format: (driver, laps, team_color)
        session_data.race_distance,
        height=450,
        show_all_drivers=show_all,
        all_drivers_laps=session_data.laps if show_all else None,
    )
    st.plotly_chart(position_fig, use_container_width=True)

    st.divider()

    # Tire Strategy Timeline
    st.subheader("🛞 Tire Strategy Timeline")

    tire_timeline_fig = create_tire_timeline(
        drivers_to_analyze,
        session_data.race_distance,
        height=200 * len(drivers_to_analyze),
    )
    st.plotly_chart(tire_timeline_fig, use_container_width=True)

    # Stint Summary Tables
    st.subheader("📋 Stint Summary")

    if len(drivers_to_analyze) == 1:
        stint_table = create_simple_stint_table(driver_1, driver_1_laps)
        if not stint_table.empty:
            st.dataframe(stint_table, use_container_width=True, hide_index=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{driver_1}**")
            stint_table_1 = create_simple_stint_table(driver_1, driver_1_laps)
            if not stint_table_1.empty:
                st.dataframe(stint_table_1, use_container_width=True, hide_index=True)

        with col2:
            st.markdown(f"**{driver_2}**")
            stint_table_2 = create_simple_stint_table(driver_2, driver_2_laps)
            if not stint_table_2.empty:
                st.dataframe(stint_table_2, use_container_width=True, hide_index=True)

    st.divider()

    # Lap Time Degradation
    st.subheader("📉 Lap Time Degradation")

    degradation_fig = create_degradation_chart(
        drivers_for_degradation,
        height=500,
    )
    st.plotly_chart(degradation_fig, use_container_width=True)

    # Degradation Metrics
    st.subheader("🔍 Degradation Metrics")

    if len(drivers_to_analyze) == 1:
        deg_summary = get_stint_degradation_summary(driver_1_laps)
        if not deg_summary.empty:
            st.dataframe(deg_summary, use_container_width=True, hide_index=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{driver_1}**")
            deg_summary_1 = get_stint_degradation_summary(driver_1_laps)
            if not deg_summary_1.empty:
                st.dataframe(deg_summary_1, use_container_width=True, hide_index=True)

        with col2:
            st.markdown(f"**{driver_2}**")
            deg_summary_2 = get_stint_degradation_summary(driver_2_laps)
            if not deg_summary_2.empty:
                st.dataframe(deg_summary_2, use_container_width=True, hide_index=True)

    # Head-to-Head Comparison (if comparing)
    if len(drivers_to_analyze) == 2 and driver_2:
        st.divider()
        render_head_to_head_comparison(driver_1, driver_1_laps, driver_2, driver_2_laps)

        # Sector Analysis (comparison mode only)
        st.divider()
        render_sector_analysis(driver_1, driver_1_laps, driver_2, driver_2_laps)


def render_head_to_head_comparison(
    driver_1: str,
    driver_1_laps: pd.DataFrame,
    driver_2: str,
    driver_2_laps: pd.DataFrame,
) -> None:
    """Render head-to-head comparison analysis."""
    from analysis.comparison import compare_stints, get_head_to_head_summary
    from utils.helpers import format_time_delta

    st.subheader("⚔️ Head-to-Head Comparison")

    summary = get_head_to_head_summary(driver_1, driver_1_laps, driver_2, driver_2_laps)

    if not summary:
        st.warning("Unable to generate comparison - insufficient data")
        return

    # Display key comparison metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Laps Won",
            f"{driver_1}: {summary['driver1_faster_laps']}",
            delta=f"{driver_2}: {summary['driver2_faster_laps']}",
            delta_color="off",
        )

    with col2:
        delta_text = format_time_delta(pd.Timedelta(seconds=summary["avg_pace_delta"]))
        st.metric(
            "Avg Pace Delta",
            delta_text,
            help=f"Negative = {driver_1} faster, Positive = {driver_2} faster",
        )

    with col3:
        fastest_delta = format_time_delta(pd.Timedelta(seconds=summary["fastest_lap_delta"]))
        st.metric(
            "Fastest Lap Delta",
            fastest_delta,
            help="Difference in fastest lap times",
        )

    with col4:
        pit_delta = format_time_delta(pd.Timedelta(seconds=summary["pit_time_delta"]))
        st.metric(
            "Pit Time Delta",
            pit_delta,
            help="Total time difference in pit stops",
        )

    # Strategy comparison
    st.markdown("#### Strategy Comparison")
    strategy_comparison = compare_stints(driver_1_laps, driver_2_laps)
    if not strategy_comparison.empty:
        st.dataframe(strategy_comparison, use_container_width=True, hide_index=True)


def render_key_insights(
    driver_1: str,
    driver_1_laps: pd.DataFrame,
    driver_2: Optional[str],
    driver_2_laps: Optional[pd.DataFrame],
) -> None:
    """Render key insights panel."""
    from analysis.insights import (
        format_insights_for_display,
        generate_race_insights,
    )

    st.subheader("💡 Key Insights")

    # Generate insights
    comparison_laps = driver_2_laps if driver_2 and driver_2_laps is not None else None
    insights = generate_race_insights(driver_1_laps, comparison_laps)

    if not insights:
        st.info("No significant insights detected for this selection.")
        return

    # Format insights for display
    formatted = format_insights_for_display(insights)

    # Display insights in columns by category
    insight_categories = [
        ("comparison", "⚔️ Comparison", "#E8F4F8"),
        ("strategy", "🔧 Strategy", "#FFF3E0"),
        ("degradation", "📉 Degradation", "#FBE9E7"),
        ("pace", "⚡ Pace", "#E8F5E9"),
    ]

    # Filter to categories with insights
    active_categories = [
        (key, title, color) for key, title, color in insight_categories
        if formatted.get(key)
    ]

    if not active_categories:
        st.info("No significant insights detected for this selection.")
        return

    # Display top insights (limit to most important)
    all_insights_flat = []
    for key, _, _ in active_categories:
        for icon, message in formatted[key]:
            all_insights_flat.append((icon, message))

    # Show top insights (max 6)
    displayed = all_insights_flat[:6]

    for icon, message in displayed:
        st.markdown(f"{icon} {message}")

    # Optionally show more in expander
    if len(all_insights_flat) > 6:
        with st.expander(f"Show all insights ({len(all_insights_flat)} total)"):
            for icon, message in all_insights_flat[6:]:
                st.markdown(f"{icon} {message}")


def render_sector_analysis(
    driver_1: str,
    driver_1_laps: pd.DataFrame,
    driver_2: str,
    driver_2_laps: pd.DataFrame,
) -> None:
    """Render sector time comparison analysis."""
    from analysis.sectors import (
        get_sector_comparison_summary,
        identify_weak_sectors,
    )
    from visualization.sector_chart import (
        create_sector_advantage_chart,
        create_sector_delta_chart,
        create_sector_scatter,
    )

    st.subheader("🏁 Sector Analysis")

    # Quick summary of sector advantages
    weak_sectors = identify_weak_sectors(driver_1_laps, driver_2_laps)

    if weak_sectors.get("summary"):
        st.info(f"📊 **Summary:** {weak_sectors['summary']}")

    # Sector advantage visualization
    advantage_fig = create_sector_advantage_chart(driver_1_laps, driver_2_laps, height=250)
    st.plotly_chart(advantage_fig, use_container_width=True)

    # Detailed sector analysis in expander
    with st.expander("📈 Detailed Sector Comparison", expanded=False):
        # Sector comparison table
        st.markdown("#### Sector Performance Summary")
        sector_summary = get_sector_comparison_summary(driver_1_laps, driver_2_laps)
        if not sector_summary.empty:
            st.dataframe(sector_summary, use_container_width=True, hide_index=True)

        # Sector times scatter plot
        st.markdown("#### Sector Times Over Race")
        scatter_fig = create_sector_scatter(driver_1_laps, driver_2_laps, height=400)
        st.plotly_chart(scatter_fig, use_container_width=True)

        # Lap-by-lap sector deltas
        st.markdown("#### Sector Delta per Lap")
        delta_fig = create_sector_delta_chart(driver_1_laps, driver_2_laps, height=350)
        st.plotly_chart(delta_fig, use_container_width=True)


if __name__ == "__main__":
    main()

