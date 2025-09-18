# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL org.opencontainers.image.authors="N H Padma Priya"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY pyproject.toml /app/
COPY src /app/src
COPY requirements.txt /app/requirements.txt

# Install deps
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir -e /app

# Runtime dirs
RUN mkdir -p /app/data /app/plots /app/reports

ENV PYTHONUNBUFFERED=1

# Default command runs CLI in non-interactive mode using env LAST_TEAM_ABBR
CMD ["python", "-m", "nba_warriors_analysis.cli", "--non-interactive"]
