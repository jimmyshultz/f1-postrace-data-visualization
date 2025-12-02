"""Tests for sector time analysis."""

from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go

from analysis.sectors import (
    SectorSummary,
    get_sector_comparison,
    get_sector_comparison_summary,
    get_sector_summary,
    get_sector_times,
    identify_weak_sectors,
)
from visualization.sector_chart import (
    create_sector_advantage_chart,
    create_sector_delta_chart,
    create_sector_scatter,
)


def create_sample_sector_laps(driver: str = "VER", team: str = "Red Bull Racing") -> pd.DataFrame:
    """Create sample lap data with sector times."""
    return pd.DataFrame(
        {
            "Driver": [driver] * 10,
            "Team": [team] * 10,
            "LapNumber": list(range(1, 11)),
            "Sector1Time": [timedelta(seconds=28 + i * 0.1) for i in range(10)],
            "Sector2Time": [timedelta(seconds=35 + i * 0.05) for i in range(10)],
            "Sector3Time": [timedelta(seconds=25 + i * 0.08) for i in range(10)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
        }
    )


def create_two_driver_sector_laps() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create sector laps for two drivers with different performance."""
    driver1_laps = pd.DataFrame(
        {
            "Driver": ["VER"] * 10,
            "Team": ["Red Bull Racing"] * 10,
            "LapNumber": list(range(1, 11)),
            "Sector1Time": [timedelta(seconds=28.0)] * 10,  # Consistent S1
            "Sector2Time": [timedelta(seconds=35.0)] * 10,  # Consistent S2
            "Sector3Time": [timedelta(seconds=25.0)] * 10,  # Consistent S3
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
        }
    )

    driver2_laps = pd.DataFrame(
        {
            "Driver": ["HAM"] * 10,
            "Team": ["Mercedes"] * 10,
            "LapNumber": list(range(1, 11)),
            "Sector1Time": [timedelta(seconds=28.2)] * 10,  # 0.2s slower in S1
            "Sector2Time": [timedelta(seconds=34.8)] * 10,  # 0.2s faster in S2
            "Sector3Time": [timedelta(seconds=25.1)] * 10,  # 0.1s slower in S3
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
        }
    )

    return driver1_laps, driver2_laps


class TestGetSectorTimes:
    """Tests for get_sector_times function."""

    def test_extracts_sector_times(self) -> None:
        """Test basic sector time extraction."""
        laps = create_sample_sector_laps()

        sector_times = get_sector_times(laps)

        assert not sector_times.empty
        assert "Sector1" in sector_times.columns
        assert "Sector2" in sector_times.columns
        assert "Sector3" in sector_times.columns
        assert len(sector_times) == 10

    def test_converts_to_seconds(self) -> None:
        """Test that timedeltas are converted to seconds."""
        laps = create_sample_sector_laps()

        sector_times = get_sector_times(laps)

        # First sector should be around 28 seconds
        assert 27 < sector_times.iloc[0]["Sector1"] < 29

    def test_includes_compound(self) -> None:
        """Test that compound is included when available."""
        laps = create_sample_sector_laps()

        sector_times = get_sector_times(laps)

        assert "Compound" in sector_times.columns

    def test_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_laps = pd.DataFrame()

        sector_times = get_sector_times(empty_laps)

        assert sector_times.empty


class TestGetSectorSummary:
    """Tests for get_sector_summary function."""

    def test_returns_summaries(self) -> None:
        """Test that summaries are returned for each sector."""
        laps = create_sample_sector_laps()

        summaries = get_sector_summary(laps)

        assert len(summaries) == 3
        assert all(isinstance(s, SectorSummary) for s in summaries)

    def test_summary_values(self) -> None:
        """Test that summary values are calculated correctly."""
        laps = create_sample_sector_laps()

        summaries = get_sector_summary(laps)

        # Check sector 1
        s1 = summaries[0]
        assert s1.sector == 1
        assert s1.best_time < s1.avg_time < s1.worst_time
        assert s1.best_lap == 1  # First lap has fastest time (28.0s)

    def test_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_laps = pd.DataFrame()

        summaries = get_sector_summary(empty_laps)

        assert len(summaries) == 0


class TestGetSectorComparison:
    """Tests for get_sector_comparison function."""

    def test_compares_two_drivers(self) -> None:
        """Test basic sector comparison."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        comparison = get_sector_comparison(driver1_laps, driver2_laps)

        assert not comparison.empty
        assert "LapNumber" in comparison.columns
        assert "S1_Delta" in comparison.columns
        assert "S2_Delta" in comparison.columns
        assert "S3_Delta" in comparison.columns

    def test_delta_calculation(self) -> None:
        """Test that deltas are calculated correctly."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        comparison = get_sector_comparison(driver1_laps, driver2_laps)

        # S1: VER is faster by 0.2s, so delta should be negative
        assert comparison.iloc[0]["S1_Delta"] < 0

        # S2: HAM is faster by 0.2s, so delta should be positive
        assert comparison.iloc[0]["S2_Delta"] > 0

    def test_empty_dataframes(self) -> None:
        """Test with empty DataFrames."""
        empty = pd.DataFrame()
        laps = create_sample_sector_laps()

        result1 = get_sector_comparison(empty, laps)
        result2 = get_sector_comparison(laps, empty)

        assert result1.empty
        assert result2.empty


class TestIdentifyWeakSectors:
    """Tests for identify_weak_sectors function."""

    def test_identifies_advantages(self) -> None:
        """Test sector advantage identification."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        result = identify_weak_sectors(driver1_laps, driver2_laps)

        assert "driver1_advantage_sectors" in result
        assert "driver2_advantage_sectors" in result
        assert "sector_deltas" in result
        assert "summary" in result

        # VER should have advantage in S1 (faster by 0.2s)
        assert 1 in result["driver1_advantage_sectors"]

        # HAM should have advantage in S2 (faster by 0.2s)
        assert 2 in result["driver2_advantage_sectors"]

    def test_summary_text(self) -> None:
        """Test that summary text is generated."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        result = identify_weak_sectors(driver1_laps, driver2_laps)

        # Summary should contain driver names and gains
        assert result["summary"] != ""
        assert "Sector" in result["summary"]


class TestGetSectorComparisonSummary:
    """Tests for get_sector_comparison_summary function."""

    def test_creates_summary_table(self) -> None:
        """Test summary table creation."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        summary = get_sector_comparison_summary(driver1_laps, driver2_laps)

        assert not summary.empty
        assert len(summary) == 3  # One row per sector
        assert "Sector" in summary.columns

    def test_empty_dataframes(self) -> None:
        """Test with empty DataFrames."""
        empty = pd.DataFrame()
        laps = create_sample_sector_laps()

        result = get_sector_comparison_summary(empty, laps)

        assert result.empty


class TestCreateSectorDeltaChart:
    """Tests for create_sector_delta_chart function."""

    def test_creates_figure(self) -> None:
        """Test that function returns a Plotly Figure."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_delta_chart(driver1_laps, driver2_laps)

        assert isinstance(fig, go.Figure)

    def test_has_sector_traces(self) -> None:
        """Test that chart has traces for each sector."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_delta_chart(driver1_laps, driver2_laps)

        # Should have 3 bar traces (one per sector)
        assert len(fig.data) >= 3

    def test_empty_dataframes(self) -> None:
        """Test with empty DataFrames."""
        empty = pd.DataFrame()
        laps = create_sample_sector_laps()

        fig = create_sector_delta_chart(empty, laps)

        assert isinstance(fig, go.Figure)


class TestCreateSectorScatter:
    """Tests for create_sector_scatter function."""

    def test_creates_figure(self) -> None:
        """Test that function returns a Plotly Figure."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_scatter(driver1_laps, driver2_laps)

        assert isinstance(fig, go.Figure)

    def test_has_subplots(self) -> None:
        """Test that chart has 3 subplots (one per sector)."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_scatter(driver1_laps, driver2_laps)

        # Should have traces for both drivers in each sector
        assert len(fig.data) >= 6  # 2 drivers * 3 sectors


class TestCreateSectorAdvantageChart:
    """Tests for create_sector_advantage_chart function."""

    def test_creates_figure(self) -> None:
        """Test that function returns a Plotly Figure."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_advantage_chart(driver1_laps, driver2_laps)

        assert isinstance(fig, go.Figure)

    def test_shows_all_sectors(self) -> None:
        """Test that chart shows all three sectors."""
        driver1_laps, driver2_laps = create_two_driver_sector_laps()

        fig = create_sector_advantage_chart(driver1_laps, driver2_laps)

        # Should have 3 bar traces (one per sector)
        assert len(fig.data) >= 3

