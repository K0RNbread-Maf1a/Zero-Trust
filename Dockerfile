# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for qrcode/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libjpeg-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false \
 && poetry install --no-root --only main

COPY . /app

EXPOSE 8000
ENV HOST=0.0.0.0 PORT=8000
CMD ["python", "server/protected_server.py"]
