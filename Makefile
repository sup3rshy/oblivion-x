PYTHON ?= .venv/bin/python
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff

.PHONY: help install test test-cov lint format check corpus build-corpus pipeline eval report clean

help:
	@echo "Oblivion-X targets"
	@echo "  make install        install the package with dev dependencies"
	@echo "  make corpus         generate corpus sources + ground truth"
	@echo "  make build-corpus   package sources into .docm/.xlsm (offline, no Office)"
	@echo "  make pipeline       run static + dynamic + reconstruction"
	@echo "  make eval           run experiments E1-E8"
	@echo "  make report         render outputs/report.md + figures"
	@echo "  make test           run the test suite"
	@echo "  make test-cov       run tests with coverage"
	@echo "  make lint           run ruff"
	@echo "  make check          lint + tests"
	@echo "  make clean          remove caches and build artifacts"

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTEST) -q

test-cov:
	$(PYTEST) -q --cov=oblivionx --cov-report=term-missing

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

check: lint test

corpus:
	$(PYTHON) -m oblivionx corpus generate --out outputs/corpus

build-corpus:
	$(PYTHON) -m oblivionx corpus build --corpus outputs/corpus

pipeline:
	$(PYTHON) -m oblivionx pipeline run --corpus outputs/corpus --out outputs/analysis

eval:
	$(PYTHON) -m oblivionx eval all --corpus outputs/corpus --analysis outputs/analysis --out outputs/eval

report:
	$(PYTHON) -m oblivionx report --eval outputs/eval --out outputs/report.md --figures outputs/figures

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info
	find . -path ./.venv -prune -o -type d -name __pycache__ -print0 | xargs -0 rm -rf
