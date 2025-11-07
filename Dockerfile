# Stage 1: Dependency installation using uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

# Create non-root user and group
ARG APP_UID=1000
ARG APP_GID=1000
RUN addgroup --gid $APP_GID appgroup && \
    adduser --disabled-password --gecos "" --uid $APP_UID --gid $APP_GID appuser
USER appuser:appgroup

WORKDIR /app

# Copy metadata and ensure src exists to satisfy setuptools
COPY --chown=appuser:appgroup pyproject.toml README.md LICENSE uv.lock /app/
RUN mkdir -p /app/src && chown appuser:appgroup /app/src

# Install dependencies, cache to temp directory
RUN mkdir -p /tmp/uv_cache && chown appuser:appgroup /tmp/uv_cache
RUN --mount=type=cache,target=/tmp/uv_cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=LICENSE,target=LICENSE \
    uv sync --frozen --no-dev --no-editable

COPY --chown=appuser:appgroup ./src/mcp_outline /app/mcp_outline

# Stage 2: Final runtime image
FROM python:3.12-slim-bookworm

# Create non-root user and group
ARG APP_UID=1000
ARG APP_GID=1000
RUN addgroup --gid $APP_GID appgroup && \
    adduser --disabled-password --gecos "" --uid $APP_UID --gid $APP_GID appuser

WORKDIR /app

# Copy the installed virtual environment and code from builder stage
COPY --chown=appuser:appgroup --from=uv /app/.venv /app/.venv
COPY --chown=appuser:appgroup --from=uv /app /app

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV MCP_HOST=0.0.0.0

# Switch to non-root user
USER appuser:appgroup

ENTRYPOINT ["mcp-outline"]
