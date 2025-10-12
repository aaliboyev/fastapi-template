# ---------- base: essentials ----------
FROM python:3.13.5-slim-bookworm AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app
COPY pyproject.toml uv.lock ./
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-editable

# ---------- runtime ----------
FROM base AS runtime
WORKDIR /app
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable --group api
COPY src ./src
COPY scripts/entrypoint.sh ./scripts/
ENTRYPOINT ["bash", "scripts/entrypoint.sh"]

# ---------- migrate ----------
FROM base AS migrate
WORKDIR /app
ENV APPLY_MIGRATIONS=1
RUN --mount=from=ghcr.io/astral-sh/uv:latest,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable --group migrate
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts/prestart.sh ./scripts/
CMD ["bash", "scripts/prestart.sh"]
