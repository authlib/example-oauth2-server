# syntax=docker/dockerfile:1@sha256:4edf897a3ffa55b89f906fc8cc78afdb3f1834cc9c7083565e611a8a7d5fe99e
FROM ghcr.io/astral-sh/uv:python3.15-trixie-slim@sha256:1017e944d8b320412287a572b8221cda45742348d0feb99e500f1f4c4b019206 AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable


FROM python:3.15-slim-trixie@sha256:8c13a3f37a6a5b71498228e902c4b9f51c1f7900d49fabf71f9a650c6120e0d0

RUN useradd -m -u 1000 appuser \
    && mkdir /data \
    && chown appuser:appuser /data

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV FLASK_RUN_HOST="0.0.0.0"
ENV FLASK_RUN_PORT="5000"
ENV FLASK_DEBUG="False"
ENV DATABASE_URL="sqlite:////data/db.sqlite"

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --start-interval=1s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/').read()" || exit 1

CMD ["authlib-server-demo"]
