# Ubuntu 24.04 (noble) — same OS as the original Playwright base image, officially
# supported by `playwright install --with-deps`. Only Chromium is installed
# (bot renders via chromium.launch() only; Firefox/WebKit are unused).
FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip ca-certificates && \
    rm -f /usr/lib/python3.12/EXTERNALLY-MANAGED && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    rm -rf /var/lib/apt/lists/*

# uv for dependency management.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps first for layer caching.
COPY pyproject.toml ./
RUN uv pip install --system .

# Only Chromium + its OS deps — skip Firefox/WebKit, unused by this bot.
RUN python -m playwright install --with-deps chromium

COPY . .

# SQLite volume mount point.
RUN mkdir -p /app/data
VOLUME ["/app/data"]

CMD ["python", "main.py"]
