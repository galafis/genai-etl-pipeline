.PHONY: install data run test lint docker clean help

help:
	@echo "GenAI ETL Pipeline - Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make data     - Generate synthetic data"
	@echo "  make run      - Run the pipeline"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linting"
	@echo "  make docker   - Build and run Docker"
	@echo "  make clean    - Clean generated files"

install:
	pip install -r requirements.txt

data:
	python src/data/generate_synthetic_data.py

run:
	python src/main.py

test:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	flake8 src/ tests/ --max-line-length=100
	mypy src/ --ignore-missing-imports
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

docker:
	docker-compose up --build

clean:
	rm -rf data/output/*
	rm -rf data/raw/*
	rm -rf logs/*
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
