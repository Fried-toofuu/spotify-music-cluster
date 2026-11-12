# Reproducible runtime for the Acoustic Observatory.
# The artifact bundle is mounted read-only at runtime; it is never baked in.
FROM python:3.12.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system --gid 10001 observatory \
    && useradd --system --uid 10001 --gid observatory --create-home observatory \
    && mkdir -p /artifacts /tmp/acoustic-observatory-assets \
    && chown -R observatory:observatory /artifacts /tmp/acoustic-observatory-assets

COPY pyproject.toml README.md MANIFEST.in constraints.txt ./
COPY src ./src

RUN python -m pip install --upgrade "pip>=26.2.2" \
    && python -m pip install ".[api,web]" -c constraints.txt

USER observatory

EXPOSE 7860
CMD ["python", "-m", "spotify_cluster.web.app"]
