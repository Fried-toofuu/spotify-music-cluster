# Render free Docker web service. Artifacts are downloaded from the private
# Hugging Face dataset at startup; none are baked into this image.
FROM python:3.12.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system --gid 10001 observatory \
    && useradd --system --uid 10001 --gid observatory --create-home observatory

COPY pyproject.toml constraints.txt MANIFEST.in README.md ./
COPY src ./src

RUN python -m pip install --upgrade "pip>=26.2.2" \
    && python -m pip install ".[api,web,deploy]" -c constraints.txt

COPY deploy/entrypoint.sh ./entrypoint.sh
RUN sed -i 's/\r$//' entrypoint.sh \
    && chmod +x entrypoint.sh \
    && chown -R observatory:observatory /app

USER observatory
EXPOSE 7860
CMD ["./entrypoint.sh"]
