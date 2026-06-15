# Playwright base image ships Chromium + system deps; pin to a recent version.
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# uv for dependency management.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps first for layer caching.
COPY pyproject.toml ./
RUN uv pip install --system .

# Chromium is preinstalled in the base image; ensure browser binaries are present.
RUN python -m playwright install chromium

COPY . .

# SQLite volume mount point.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD ["python", "main.py"]
