# syntax=docker/dockerfile:1.7
# Single-container build for Coolify.
# Runs Streamlit + FastAPI + Next.js static landing behind an internal Nginx router.
# Coolify handles TLS and the public-facing proxy — this container serves on port 80.

# ---- Stage 1: Build Next.js landing (static export → out/) ----
FROM node:20-alpine AS landing-builder
WORKDIR /landing
COPY landing/package.json landing/package-lock.json* ./
RUN npm ci --prefer-offline
COPY landing/ ./
ENV NODE_ENV=production
RUN npm run build

# ---- Stage 2: Build Python dependencies ----
FROM python:3.11-slim-bookworm AS py-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---- Stage 3: Runtime ----
FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python app + virtualenv
COPY --from=py-builder /app /app

# Next.js static output
COPY --from=landing-builder /landing/out /var/www/landing

# Nginx and supervisord configs
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/app.conf

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 80

HEALTHCHECK CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost/api/health').read()" \
    || exit 1

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
