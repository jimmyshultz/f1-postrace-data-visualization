.PHONY: install dev test lint format run clean

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov

lint:
	ruff check .
	mypy .

format:
	ruff format .

run:
	streamlit run app.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/