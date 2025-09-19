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
# Optional seed data: not bundled in image to avoid build failures when data/ absent

# Install deps
RUN pip install --no-cache-dir -r /app/requirements.txt && \
    pip install --no-cache-dir -e /app

# Runtime dirs (ensure seed dir exists even if no data is bundled)
RUN mkdir -p /app/data /app/plots /app/reports /app/data_seed

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV PYTHONPATH=/app/src:${PYTHONPATH}

# Start the web app with Gunicorn (Render ignores Procfile for Docker services)
EXPOSE 8000
CMD gunicorn "nba_warriors_analysis.webapp:create_app()" -b 0.0.0.0:${PORT} --worker-tmp-dir /dev/shm --workers ${GUNICORN_WORKERS:-2} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-120}
