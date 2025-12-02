"""Tests for position chart visualization."""

from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from visualization.position_chart import (
    _extract_position_data,
    create_position_chart,
    get_position_summary,
)


def create_sample_position_laps() -> pd.DataFrame:
    """Create sample lap data with position changes."""
    return pd.DataFrame(
        {
            "Driver": ["VER"] * 15,
            "Team": ["Red Bull Racing"] * 15,
            "LapNumber": list(range(1, 16)),
            "LapTime": [timedelta(seconds=90) for _ in range(15)],
            "Position": [3, 3, 2, 2, 2, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1],
            "PitInTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 10,
            "PitOutTime": [None] * 5 + [pd.Timestamp("2024-01-01 12:00:03")]
            + [None] * 9,
        }
    )


def create_sample_two_drivers() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create sample lap data for two drivers."""
    driver1_laps = pd.DataFrame(
        {
            "Driver": ["VER"] * 10,
            "Team": ["Red Bull Racing"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90) for _ in range(10)],
            "Position": [2, 2, 2, 2, 1, 1, 1, 1, 1, 1],
            "PitInTime": [None] * 3 + [pd.Timestamp("2024-01-01 12:00:00")]
            + [None] * 6,
            "PitOutTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:02.5")]
            + [None] * 5,
        }
    )

    driver2_laps = pd.DataFrame(
        {
            "Driver": ["HAM"] * 10,
            "Team": ["Mercedes"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90.5) for _ in range(10)],
            "Position": [1, 1, 1, 1, 2, 2, 2, 2, 2, 2],
            "PitInTime": [None] * 3 + [pd.Timestamp("2024-01-01 12:00:01")]
            + [None] * 6,
            "PitOutTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:03.5")]
            + [None] * 5,
        }
    )

    return driver1_laps, driver2_laps


class TestCreatePositionChart:
    """Tests for create_position_chart function."""

    def test_creates_figure(self) -> None:
        """Test that function returns a Plotly Figure."""
        laps = create_sample_position_laps()
        driver_laps_list = [("VER", laps, "#3671C6")]

        fig = create_position_chart(driver_laps_list, race_distance=15)

        assert isinstance(fig, go.Figure)

    def test_single_driver(self) -> None:
        """Test chart with single driver."""
        laps = create_sample_position_laps()
        driver_laps_list = [("VER", laps, "#3671C6")]

        fig = create_position_chart(driver_laps_list, race_distance=15)

        # Should have at least one trace for the driver
        assert len(fig.data) >= 1
        assert fig.data[0].name == "VER"

    def test_two_drivers(self) -> None:
        """Test chart with two drivers."""
        driver1_laps, driver2_laps = create_sample_two_drivers()
        driver_laps_list = [
            ("VER", driver1_laps, "#3671C6"),
            ("HAM", driver2_laps, "#27F4D2"),
        ]

        fig = create_position_chart(driver_laps_list, race_distance=10)

        # Should have traces for both drivers
        driver_names = [trace.name for trace in fig.data if trace.name in ["VER", "HAM"]]
        assert "VER" in driver_names
        assert "HAM" in driver_names

    def test_empty_laps(self) -> None:
        """Test chart handles empty laps gracefully."""
        empty_laps = pd.DataFrame()
        driver_laps_list = [("VER", empty_laps, "#3671C6")]

        fig = create_position_chart(driver_laps_list, race_distance=10)

        assert isinstance(fig, go.Figure)

    def test_chart_layout(self) -> None:
        """Test chart has correct layout configuration."""
        laps = create_sample_position_laps()
        driver_laps_list = [("VER", laps, "#3671C6")]

        fig = create_position_chart(driver_laps_list, race_distance=15, height=600)

        assert fig.layout.title.text == "Position Changes Throughout Race"
        assert fig.layout.xaxis.title.text == "Lap Number"
        assert fig.layout.yaxis.title.text == "Position"
        assert fig.layout.height == 600
        # Y-axis should be inverted (P1 at top)
        assert fig.layout.yaxis.range[0] > fig.layout.yaxis.range[1]

    def test_pit_stop_markers(self) -> None:
        """Test that pit stops are marked on the chart."""
        laps = create_sample_position_laps()
        driver_laps_list = [("VER", laps, "#3671C6")]

        fig = create_position_chart(driver_laps_list, race_distance=15)

        # Should have pit stop marker traces
        # Main trace + pit stop marker trace
        assert len(fig.data) >= 2

    def test_no_team_color_provided(self) -> None:
        """Test chart uses extracted team color when none provided."""
        laps = create_sample_position_laps()
        driver_laps_list = [("VER", laps, None)]

        fig = create_position_chart(driver_laps_list, race_distance=15)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1


class TestExtractPositionData:
    """Tests for _extract_position_data function."""

    def test_extracts_positions(self) -> None:
        """Test position data extraction."""
        laps = create_sample_position_laps()

        lap_numbers, positions = _extract_position_data(laps)

        assert len(lap_numbers) == 15
        assert len(positions) == 15
        assert lap_numbers[0] == 1
        assert positions[0] == 3

    def test_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_laps = pd.DataFrame()

        lap_numbers, positions = _extract_position_data(empty_laps)

        assert lap_numbers == []
        assert positions == []

    def test_missing_position_column(self) -> None:
        """Test with DataFrame missing Position column."""
        laps = pd.DataFrame({"LapNumber": [1, 2, 3]})

        lap_numbers, positions = _extract_position_data(laps)

        assert lap_numbers == []
        assert positions == []

    def test_filters_nan_positions(self) -> None:
        """Test that NaN positions are filtered out."""
        laps = pd.DataFrame(
            {
                "LapNumber": [1, 2, 3, 4, 5],
                "Position": [1, None, 2, None, 3],
            }
        )

        lap_numbers, positions = _extract_position_data(laps)

        assert len(lap_numbers) == 3
        assert len(positions) == 3


class TestGetPositionSummary:
    """Tests for get_position_summary function."""

    def test_calculates_summary(self) -> None:
        """Test position summary calculation."""
        laps = create_sample_position_laps()

        summary = get_position_summary(laps)

        assert summary["start_position"] == 3
        assert summary["end_position"] == 1
        assert summary["best_position"] == 1
        assert summary["worst_position"] == 3
        assert summary["positions_gained"] == 2  # P3 -> P1

    def test_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_laps = pd.DataFrame()

        summary = get_position_summary(empty_laps)

        assert summary["start_position"] is None
        assert summary["end_position"] is None
        assert summary["positions_gained"] is None

    def test_position_changes_count(self) -> None:
        """Test counting of position changes."""
        laps = pd.DataFrame(
            {
                "LapNumber": [1, 2, 3, 4, 5],
                "Position": [1, 2, 1, 2, 1],  # 4 position changes
            }
        )

        summary = get_position_summary(laps)

        assert summary["position_changes"] == 4

    def test_no_position_changes(self) -> None:
        """Test when driver maintains same position."""
        laps = pd.DataFrame(
            {
                "LapNumber": [1, 2, 3, 4, 5],
                "Position": [1, 1, 1, 1, 1],
            }
        )

        summary = get_position_summary(laps)

        assert summary["position_changes"] == 0
        assert summary["positions_gained"] == 0

