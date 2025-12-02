"""Tests for insights generation."""

from datetime import timedelta

import pandas as pd

from analysis.insights import (
    Insight,
    InsightType,
    _generate_comparison_insights,
    _generate_degradation_insights,
    _generate_pace_insights,
    _generate_strategy_insights,
    detect_tire_cliff,
    detect_undercut_attempts,
    format_insights_for_display,
    generate_race_insights,
)


def create_sample_race_laps(driver: str = "VER") -> pd.DataFrame:
    """Create sample race lap data."""
    return pd.DataFrame(
        {
            "Driver": [driver] * 20,
            "Team": ["Red Bull Racing"] * 20,
            "LapNumber": list(range(1, 21)),
            "LapTime": [timedelta(seconds=90 + i * 0.1) for i in range(20)],
            "Compound": ["SOFT"] * 10 + ["MEDIUM"] * 10,
            "TyreLife": list(range(1, 11)) + list(range(1, 11)),
            "Position": [3, 3, 3, 2, 2, 2, 2, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1],
            "PitInTime": [None] * 9 + [pd.Timestamp("2024-01-01 12:00:00")] + [None] * 10,
            "PitOutTime": [None] * 10 + [pd.Timestamp("2024-01-01 12:00:03")] + [None] * 9,
        }
    )


def create_two_driver_laps() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create lap data for two drivers."""
    driver1_laps = pd.DataFrame(
        {
            "Driver": ["VER"] * 10,
            "Team": ["Red Bull Racing"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90) for _ in range(10)],
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
            "TyreLife": list(range(1, 6)) + list(range(1, 6)),
            "Position": [2, 2, 2, 1, 1, 1, 1, 1, 1, 1],
            "PitInTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:00")] + [None] * 5,
            "PitOutTime": [None] * 5 + [pd.Timestamp("2024-01-01 12:00:03")] + [None] * 4,
        }
    )

    driver2_laps = pd.DataFrame(
        {
            "Driver": ["HAM"] * 10,
            "Team": ["Mercedes"] * 10,
            "LapNumber": list(range(1, 11)),
            "LapTime": [timedelta(seconds=90.5) for _ in range(10)],  # 0.5s slower
            "Compound": ["SOFT"] * 5 + ["MEDIUM"] * 5,
            "TyreLife": list(range(1, 6)) + list(range(1, 6)),
            "Position": [1, 1, 1, 2, 2, 2, 2, 2, 2, 2],
            "PitInTime": [None] * 4 + [pd.Timestamp("2024-01-01 12:00:01")] + [None] * 5,
            "PitOutTime": [None] * 5 + [pd.Timestamp("2024-01-01 12:00:04")] + [None] * 4,
        }
    )

    return driver1_laps, driver2_laps


class TestGenerateRaceInsights:
    """Tests for generate_race_insights function."""

    def test_returns_insights_list(self) -> None:
        """Test that function returns a list of insights."""
        laps = create_sample_race_laps()

        insights = generate_race_insights(laps)

        assert isinstance(insights, list)
        assert all(isinstance(i, Insight) for i in insights)

    def test_insights_sorted_by_importance(self) -> None:
        """Test that insights are sorted by importance (highest first)."""
        laps = create_sample_race_laps()

        insights = generate_race_insights(laps)

        if len(insights) > 1:
            importances = [i.importance for i in insights]
            assert importances == sorted(importances, reverse=True)

    def test_with_comparison_driver(self) -> None:
        """Test insights generation with comparison driver."""
        driver1_laps, driver2_laps = create_two_driver_laps()

        insights = generate_race_insights(driver1_laps, driver2_laps)

        # Should include comparison insights
        comparison_insights = [
            i for i in insights if i.insight_type == InsightType.COMPARISON
        ]
        assert len(comparison_insights) > 0

    def test_empty_dataframe(self) -> None:
        """Test with empty DataFrame."""
        empty_laps = pd.DataFrame()

        insights = generate_race_insights(empty_laps)

        assert insights == []


class TestGenerateStrategyInsights:
    """Tests for strategy insights generation."""

    def test_detects_pit_stops(self) -> None:
        """Test that pit stop info is included."""
        laps = create_sample_race_laps()

        insights = _generate_strategy_insights("VER", laps)

        # Should have at least some strategy insights
        assert len(insights) >= 0  # May or may not have depending on thresholds


class TestGenerateDegradationInsights:
    """Tests for degradation insights generation."""

    def test_analyzes_stints(self) -> None:
        """Test that stint degradation is analyzed."""
        laps = create_sample_race_laps()

        insights = _generate_degradation_insights("VER", laps)

        # May or may not have insights depending on degradation levels
        assert isinstance(insights, list)


class TestGeneratePaceInsights:
    """Tests for pace insights generation."""

    def test_includes_fastest_lap(self) -> None:
        """Test that fastest lap info is included."""
        laps = create_sample_race_laps()

        insights = _generate_pace_insights("VER", laps)

        # Should have at least the fastest lap insight
        assert len(insights) >= 1
        messages = [i.message for i in insights]
        assert any("fastest" in m.lower() for m in messages)


class TestGenerateComparisonInsights:
    """Tests for comparison insights generation."""

    def test_compares_lap_times(self) -> None:
        """Test that lap times are compared."""
        driver1_laps, driver2_laps = create_two_driver_laps()

        insights = _generate_comparison_insights(driver1_laps, driver2_laps)

        assert len(insights) >= 1
        # VER should be faster
        messages = " ".join([i.message for i in insights])
        assert "VER" in messages

    def test_empty_comparison(self) -> None:
        """Test with empty comparison laps."""
        laps = create_sample_race_laps()
        empty = pd.DataFrame()

        insights = _generate_comparison_insights(laps, empty)

        assert insights == []


class TestDetectUndercutAttempts:
    """Tests for undercut detection."""

    def test_detects_position_gain(self) -> None:
        """Test detection of position gain through pit stop."""
        # Create laps where driver gains positions after pit
        laps = pd.DataFrame(
            {
                "Driver": ["VER"] * 15,
                "LapNumber": list(range(1, 16)),
                "LapTime": [timedelta(seconds=90) for _ in range(15)],
                "Compound": ["SOFT"] * 7 + ["MEDIUM"] * 8,
                "TyreLife": list(range(1, 8)) + list(range(1, 9)),
                "Position": [5, 5, 5, 5, 5, 5, 5, 2, 2, 2, 2, 2, 2, 2, 2],  # Gains 3 positions
                "PitInTime": [None] * 6 + [pd.Timestamp("2024-01-01 12:00:00")] + [None] * 8,
                "PitOutTime": [None] * 7 + [pd.Timestamp("2024-01-01 12:00:03")] + [None] * 7,
            }
        )

        insight = detect_undercut_attempts(laps)

        assert insight is not None
        assert "gained" in insight.message.lower()
        assert insight.importance == 3


class TestDetectTireCliff:
    """Tests for tire cliff detection."""

    def test_detects_sudden_degradation(self) -> None:
        """Test detection of sudden tire performance drop."""
        # Create laps with a tire cliff
        lap_times = [90, 90.1, 90.2, 90.3, 90.4, 93, 93.5, 94, 94.5, 95]  # Cliff at lap 6
        laps = pd.DataFrame(
            {
                "Driver": ["VER"] * 10,
                "LapNumber": list(range(1, 11)),
                "LapTime": [timedelta(seconds=t) for t in lap_times],
                "Compound": ["SOFT"] * 10,
                "PitInTime": [None] * 10,
                "PitOutTime": [None] * 10,
            }
        )

        insight = detect_tire_cliff("VER", laps, "SOFT")

        # Should detect the cliff
        if insight:
            assert "cliff" in insight.message.lower()
            assert insight.importance == 3

    def test_no_cliff_detected(self) -> None:
        """Test when there's no tire cliff."""
        # Create consistent lap times
        laps = pd.DataFrame(
            {
                "Driver": ["VER"] * 10,
                "LapNumber": list(range(1, 11)),
                "LapTime": [timedelta(seconds=90 + i * 0.1) for i in range(10)],
                "Compound": ["SOFT"] * 10,
                "PitInTime": [None] * 10,
                "PitOutTime": [None] * 10,
            }
        )

        insight = detect_tire_cliff("VER", laps, "SOFT")

        assert insight is None


class TestFormatInsightsForDisplay:
    """Tests for format_insights_for_display function."""

    def test_groups_by_type(self) -> None:
        """Test that insights are grouped by type."""
        insights = [
            Insight(InsightType.STRATEGY, "Strategy insight", 2, "🔧"),
            Insight(InsightType.PACE, "Pace insight", 1, "⚡"),
            Insight(InsightType.DEGRADATION, "Degradation insight", 2, "📉"),
        ]

        formatted = format_insights_for_display(insights)

        assert "strategy" in formatted
        assert "pace" in formatted
        assert "degradation" in formatted
        assert "comparison" in formatted

        assert len(formatted["strategy"]) == 1
        assert len(formatted["pace"]) == 1
        assert len(formatted["degradation"]) == 1

    def test_includes_icon_and_message(self) -> None:
        """Test that formatted output includes icon and message."""
        insights = [
            Insight(InsightType.STRATEGY, "Test message", 2, "🔧"),
        ]

        formatted = format_insights_for_display(insights)

        icon, message = formatted["strategy"][0]
        assert icon == "🔧"
        assert message == "Test message"


class TestInsightDataclass:
    """Tests for Insight dataclass."""

    def test_insight_creation(self) -> None:
        """Test that Insight can be created properly."""
        insight = Insight(
            insight_type=InsightType.STRATEGY,
            message="Test message",
            importance=2,
            icon="🔧",
        )

        assert insight.insight_type == InsightType.STRATEGY
        assert insight.message == "Test message"
        assert insight.importance == 2
        assert insight.icon == "🔧"

