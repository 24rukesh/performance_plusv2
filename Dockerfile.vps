# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM python:3.11-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# First pass: install dependencies only (cache key = lockfile only)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Copy source code
COPY . /app

# Second pass: install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- streamlit runtime stage ----
FROM python:3.11-slim-bookworm AS streamlit

# Create non-root user with home directory (-m is critical for Streamlit ~/.streamlit/ writes)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser

WORKDIR /app

# Copy built application from builder, owned by appuser
COPY --from=builder --chown=appuser:appgroup /app /app

# Add venv binaries to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

EXPOSE 8501

# Healthcheck using Python stdlib (curl not guaranteed in slim image)
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ---- api runtime stage ----
FROM python:3.11-slim-bookworm AS api

# Create non-root user with home directory
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /home/appuser -s /bin/false appuser

WORKDIR /app

# Copy built application from builder, owned by appuser
COPY --from=builder --chown=appuser:appgroup /app /app

# Add venv binaries to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER appuser

EXPOSE 8000

# Healthcheck using Python stdlib (curl not guaranteed in slim image)
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
