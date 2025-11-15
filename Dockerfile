# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN mkdir -p src
RUN uv sync --frozen --no-dev --no-install-project

COPY ./src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm

ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid $APP_GID appuser && \
    useradd --uid $APP_UID --gid $APP_GID --create-home appuser

WORKDIR /app

COPY --chown=appuser:appuser --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=3000
ENV MCP_TRANSPORT=streamable-http

USER appuser

ENTRYPOINT ["mcp-outline"]
