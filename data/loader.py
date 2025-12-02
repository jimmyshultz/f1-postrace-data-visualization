"""Data loading from FastF1."""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import fastf1
import pandas as pd
import streamlit as st

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Container for loaded F1 session data."""

    year: int
    race_name: str
    session_type: str
    session: fastf1.core.Session
    laps: pd.DataFrame
    drivers: List[str]
    race_distance: int

    def __post_init__(self) -> None:
        """Validate session data after initialization."""
        if self.laps.empty:
            logger.warning(f"No lap data available for {self.race_name} {self.session_type}")


def enable_cache() -> None:
    """Enable FastF1 caching for faster subsequent loads."""
    if settings.FASTF1_CACHE_ENABLED:
        fastf1.Cache.enable_cache(settings.FASTF1_CACHE_PATH)
        logger.info(f"FastF1 cache enabled at: {settings.FASTF1_CACHE_PATH}")


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_race_schedule(year: int) -> pd.DataFrame:
    """
    Get the race schedule for a given year.

    Args:
        year: Season year

    Returns:
        DataFrame with race schedule information

    Raises:
        Exception: If unable to fetch schedule
    """
    start_time = time.perf_counter()
    try:
        schedule = fastf1.get_event_schedule(year)
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Fetched race schedule for {year} in {elapsed:.2f}ms")
        return schedule
    except Exception as e:
        logger.error(f"Failed to fetch schedule for {year}: {e}")
        raise


def get_race_names(year: int) -> List[str]:
    """
    Get list of race names for a given year.

    Args:
        year: Season year

    Returns:
        List of race names
    """
    try:
        schedule = get_race_schedule(year)
        # Filter to only actual race events (not testing)
        races = schedule[schedule["EventFormat"] != "testing"]
        return races["EventName"].tolist()
    except Exception as e:
        logger.error(f"Failed to get race names for {year}: {e}")
        return []


def load_session(year: int, race_name: str, session_type: str) -> Optional[SessionData]:
    """
    Load an F1 session with all data.

    Args:
        year: Season year
        race_name: Name of the race (e.g., 'Bahrain Grand Prix')
        session_type: Type of session ('Race', 'Sprint', 'Qualifying', etc.)

    Returns:
        SessionData object with loaded session, or None if loading fails

    Raises:
        Exception: If session loading fails
    """
    start_time = time.perf_counter()
    enable_cache()

    logger.info(f"Loading {year} {race_name} - {session_type}")

    try:
        # Get the session
        session = fastf1.get_session(year, race_name, session_type)

        # Load all session data (laps, telemetry, etc.)
        session.load()

        # Get laps dataframe
        laps = session.laps

        if laps.empty:
            logger.warning(f"No lap data available for {year} {race_name} {session_type}")
            return None

        # Get list of drivers
        drivers = laps["Driver"].unique().tolist()

        # Get race distance (total laps)
        if "LapNumber" in laps.columns:
            race_distance = int(laps["LapNumber"].max())
        else:
            race_distance = 0

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"Successfully loaded session: {len(drivers)} drivers, "
            f"{len(laps)} laps, {race_distance} lap race in {elapsed:.2f}s"
        )

        return SessionData(
            year=year,
            race_name=race_name,
            session_type=session_type,
            session=session,
            laps=laps,
            drivers=drivers,
            race_distance=race_distance,
        )

    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise


def get_driver_laps(session_data: SessionData, driver: str) -> pd.DataFrame:
    """
    Get laps for a specific driver.

    Args:
        session_data: Loaded session data
        driver: Driver abbreviation (e.g., 'VER', 'HAM')

    Returns:
        DataFrame of laps for the driver
    """
    # Use pick_drivers (plural) to avoid deprecation warning
    driver_laps = session_data.laps.pick_drivers(driver)
    return driver_laps


def get_driver_info(session_data: SessionData) -> pd.DataFrame:
    """
    Get driver information including names and teams.

    Args:
        session_data: Loaded session data

    Returns:
        DataFrame with driver information
    """
    # Get unique driver info
    driver_info = (
        session_data.laps[["Driver", "DriverNumber", "Team", "TeamColor"]]
        .drop_duplicates(subset=["Driver"])
        .sort_values("DriverNumber")
    )

    return driver_info

