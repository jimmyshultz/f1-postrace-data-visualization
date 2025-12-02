"""Application configuration and settings."""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)

# FastF1 Settings
FASTF1_CACHE_ENABLED = True
FASTF1_CACHE_PATH = str(CACHE_DIR)

# App Settings
APP_TITLE = "F1 Strategy Analyzer"
APP_ICON = "🏎️"
DEFAULT_YEAR = 2024
DEFAULT_SESSION_TYPE = "Race"

# Available years for analysis
AVAILABLE_YEARS = list(range(2024, 2017, -1))

# Session types
SESSION_TYPES = ["Race", "Sprint", "Qualifying", "FP1", "FP2", "FP3"]

# Visualization Settings
CHART_HEIGHT = 500
CHART_THEME = "plotly"  # or "plotly_dark"

# Performance
MAX_CACHE_SIZE_GB = 10
SESSION_TIMEOUT_MINUTES = 30

# Feature Flags
ENABLE_COMPARISON = True
ENABLE_SECTOR_ANALYSIS = False  # Phase 2
ENABLE_WHAT_IF_SIMULATOR = False  # Phase 3

