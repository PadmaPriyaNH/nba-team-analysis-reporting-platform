# Simple Makefile for common tasks

.PHONY: install dev lint format test run cli docker-build docker-run

install:
	pip install -r requirements.txt
	pip install -e .

dev:
	pip install black isort flake8 pytest pre-commit
	pre-commit install

lint:
	flake8 src tests

format:
	isort src tests
	black src tests

test:
	pytest

run:
	python -m nba_warriors_analysis.cli

cli:
	python -m nba_warriors_analysis.cli --non-interactive

docker-build:
	docker build -t nba-analysis:latest .

docker-run:
	docker compose up --build
