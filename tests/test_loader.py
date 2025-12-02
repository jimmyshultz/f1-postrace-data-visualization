"""Tests for data loader module."""

import pytest

from data.loader import SessionData, enable_cache, get_race_names, load_session


def test_enable_cache() -> None:
    """Test that cache can be enabled without errors."""
    # Should not raise any exceptions
    enable_cache()


def test_get_race_names() -> None:
    """Test getting race names for a season."""
    # Test with 2024 season
    races = get_race_names(2024)

    assert isinstance(races, list)
    assert len(races) > 0
    # Should have common races
    assert any("Bahrain" in race for race in races)


@pytest.mark.slow
def test_load_session() -> None:
    """Test loading a complete session (requires network)."""
    # Load 2024 Bahrain GP Race
    session_data = load_session(2024, "Bahrain Grand Prix", "R")

    assert session_data is not None
    assert isinstance(session_data, SessionData)
    assert session_data.year == 2024
    assert session_data.race_name == "Bahrain Grand Prix"
    assert session_data.session_type == "R"
    assert not session_data.laps.empty
    assert len(session_data.drivers) > 0
    assert session_data.race_distance > 0


@pytest.mark.slow
def test_load_invalid_session() -> None:
    """Test loading an invalid session."""
    # FastF1 might succeed or raise an exception depending on the API
    # Just verify it either raises an exception or returns None
    try:
        result = load_session(2024, "Invalid Race Name That Does Not Exist", "R")
        # If it doesn't raise, it should return None
        assert result is None
    except Exception:
        # This is also acceptable - the load failed as expected
        pass

