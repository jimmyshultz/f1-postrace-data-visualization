# 🏎️ F1 Strategy Analyzer

**An interactive web-based dashboard for analyzing Formula 1 race strategies, focusing on tire strategy, lap time degradation, and comparative driver performance.**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.40.2-FF4B4B.svg)](https://streamlit.io/)
[![FastF1](https://img.shields.io/badge/FastF1-3.4.2-red.svg)](https://github.com/theOehrly/Fast-F1)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 Overview

F1 Strategy Analyzer transforms raw Formula 1 timing data into interactive visualizations that reveal strategic decisions, tire performance, and alternative strategy outcomes. Perfect for F1 enthusiasts, strategy analysts, content creators, and anyone wondering "what if they'd pitted earlier?"

### Key Features

- **📅 Session Selection**: Analyze any F1 race from 2018-2024
- **🏁 Tire Strategy Timeline**: Visual representation of pit stop strategies and tire compounds
- **📈 Lap Time Analysis**: Track tire degradation and performance over race distance
- **⚔️ Driver Comparison**: Compare strategies and pace between any two drivers
- **📊 Race Statistics**: Comprehensive stint breakdowns and performance metrics
- **🎨 Interactive Visualizations**: Zoom, hover, and explore your data with Plotly

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended)
- 10GB disk space for cache
- Internet connection for data download

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jimmyshultz/f1-postrace-data-visualization.git
   cd f1-postrace-data-visualization
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install
   # Or manually: pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   make run
   # Or manually: streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

---

## 💻 Usage

### Basic Workflow

1. **Select a Session**: Choose year, race, and session type (Race, Sprint, Qualifying)
2. **Load Data**: Click "Load Session" and wait for FastF1 to fetch the data (< 30s first time, < 2s cached)
3. **Choose Drivers**: Select one or two drivers to analyze
4. **Explore**: Interact with visualizations and review statistics

### Example Analysis

```python
# The app handles this for you, but here's what's happening under the hood:
import fastf1

fastf1.Cache.enable_cache('cache/')
session = fastf1.get_session(2024, 'Monaco', 'R')
session.load()

# Analyze Verstappen vs Leclerc
ver_laps = session.laps.pick_drivers('VER')
lec_laps = session.laps.pick_drivers('LEC')
```

---

## 📂 Project Structure

```
f1-postrace-data-visualization/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml             # Project configuration
├── Makefile                   # Common development commands
├── .cursorrules               # AI-assisted development guidelines
│
├── config/
│   └── settings.py            # App configuration (cache paths, etc)
│
├── data/
│   ├── loader.py              # FastF1 data loading & caching
│   └── preprocessor.py        # Data cleaning & transformation
│
├── analysis/
│   ├── strategy.py            # Tire strategy calculations
│   ├── degradation.py         # Lap time degradation analysis
│   └── comparison.py          # Driver comparison logic
│
├── visualization/
│   ├── tire_timeline.py       # Tire strategy timeline chart
│   └── degradation_chart.py   # Lap time degradation plots
│
└── utils/
    ├── colors.py              # Team colors, tire colors
    └── helpers.py             # Common utility functions
```

---

## 🛠️ Development

### Setup Development Environment

```bash
make dev
# Or manually: pip install -r requirements-dev.txt
```

### Available Commands

```bash
make install      # Install production dependencies
make dev          # Install development dependencies
make run          # Run the Streamlit app
make test         # Run tests with coverage
make lint         # Run ruff and mypy
make format       # Format code with ruff
make clean        # Clean cache and build artifacts
```

### Running Tests

```bash
make test
# Or manually: pytest tests/ -v --cov
```

### Code Quality

We use modern Python tooling for code quality:
- **Ruff**: Fast linting and formatting (replaces black + flake8)
- **mypy**: Static type checking with strict mode
- **pytest**: Testing framework with coverage

All configuration is in `pyproject.toml`.

---

## 🧪 Testing Sessions

Known good sessions for testing and development:

- **2024 Bahrain GP**: Standard race, good for baseline testing
- **2024 Monaco GP**: Safety car heavy, tests edge cases
- **2024 Singapore GP**: High degradation, compound differences

---

## 🗺️ Roadmap

### Phase 1: MVP ✅ Complete!
- [x] Project setup & configuration
- [x] Session selection UI
- [x] Tire strategy timeline visualization
- [x] Lap time degradation analysis
- [x] Race statistics panel (grid position, final position, positions gained/lost)
- [x] Driver comparison mode (head-to-head analysis)

### Phase 2: Enhancement
- [ ] Position changes visualization (bumps chart)
- [ ] Sector time comparison
- [ ] Enhanced insights generation
- [ ] Performance optimization

### Phase 3: Advanced Features
- [ ] What-if strategy simulator
- [ ] Historical comparisons
- [ ] Export functionality (PNG, PDF, CSV)
- [ ] Mobile responsive design

See [spec.md](spec.md) for complete technical specification.

---

## 🧰 Tech Stack

| Category | Technology |
|----------|-----------|
| **Frontend** | Streamlit 1.40.2 |
| **Data Source** | FastF1 3.4.2 |
| **Visualization** | Plotly 5.24.1 |
| **Data Processing** | Pandas 2.2.3, NumPy 2.1.3 |
| **Language** | Python 3.10+ |
| **Dev Tools** | Ruff, mypy, pytest |

---

## 📊 Performance Targets

- **Initial session load**: < 30 seconds (uncached)
- **Cached session load**: < 2 seconds  
- **Chart rendering**: < 1 second per chart
- **Dashboard refresh**: < 500ms

---

## 🤝 Contributing

Contributions are welcome! Whether it's bug fixes, new features, or documentation improvements.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style in `.cursorrules`
4. Run tests and linting (`make test lint`)
5. Format your code (`make format`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 and the guidelines in `.cursorrules`
- Use type hints for all function signatures
- Document public functions with Google-style docstrings
- Keep functions focused and single-purpose

---

## 📝 Documentation

- **[spec.md](spec.md)**: Complete technical specification with architecture, data models, and algorithms
- **[.cursorrules](.cursorrules)**: AI-assisted development guidelines and best practices
- **[LICENSE](LICENSE)**: MIT License details

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Jimmy Shultz

---

## 🙏 Acknowledgments

- **[FastF1](https://github.com/theOehrly/Fast-F1)**: Excellent F1 data access library by Oehrly
- **[Streamlit](https://streamlit.io/)**: Making data apps incredibly easy
- **[Plotly](https://plotly.com/)**: Beautiful interactive visualizations
- **F1 Community**: For inspiring this project

---

## 📧 Contact & Links

- **Project Repository**: [github.com/jimmyshultz/f1-postrace-data-visualization](https://github.com/jimmyshultz/f1-postrace-data-visualization)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/jimmyshultz/f1-postrace-data-visualization/issues)

---

## 🎮 Demo

The MVP is complete! Run the app locally to explore F1 race strategies:

```bash
streamlit run app.py
```

**Recommended test session:** 2024 Bahrain Grand Prix (Race) - Compare VER vs LEC

<!-- Future sections:
### Screenshots

![Session Selection](docs/images/session-selection.png)
![Tire Strategy](docs/images/tire-strategy.png)
![Lap Time Analysis](docs/images/lap-time-analysis.png)

### Live Demo

Try it out: [https://f1-strategy-analyzer.streamlit.app](https://f1-strategy-analyzer.streamlit.app)
-->

---

**Made with ❤️ for the F1 community**
