"""
Invariant tests for container and reverse-proxy configuration files.

Guards against:
- Pitfall 3: non-root user missing -m flag (Streamlit cannot write ~/.streamlit/)
- Pitfall 2: caddy cert volumes not named (rate-limit on every restart)
- Pitfall 5: setting only enableCORS=false causes silent CORS re-enable
- Pitfall 8: both Dockerfile stages must use the same base image
- Threat T-04-06: OPENAI_API_KEY must never be baked into image layers
"""
import re
from pathlib import Path

yaml = pytest_importorskip = None
try:
    import yaml
except ImportError:
    pass

import pytest

if yaml is None:
    pytest.importorskip("yaml", reason="pyyaml is required: run `uv add --dev pyyaml`")
    import yaml  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent

DOCKERFILE = (REPO_ROOT / "Dockerfile").read_text()
COMPOSE = yaml.safe_load((REPO_ROOT / "compose.yaml").read_text())
CADDYFILE = (REPO_ROOT / "caddy" / "Caddyfile").read_text()
STREAMLIT_CFG = (REPO_ROOT / ".streamlit" / "config.toml").read_text()
DOCKERIGNORE = (REPO_ROOT / ".dockerignore").read_text().splitlines()


def test_dockerfile_uses_python_3_11_slim_bookworm_in_both_stages():
    """Both FROM lines must use the same base image (Pitfall 8 — mismatched base breaks PATH)."""
    count = DOCKERFILE.count("FROM python:3.11-slim-bookworm")
    assert count == 2, (
        f"Expected 'FROM python:3.11-slim-bookworm' to appear exactly 2 times (builder + runtime), "
        f"found {count}. Both stages must use the identical base image (Pitfall 8)."
    )


def test_dockerfile_runs_as_non_root():
    """Runtime stage must switch to non-root user with a writable home directory (Pitfall 3, INFRA-01)."""
    assert "USER appuser" in DOCKERFILE, (
        "Dockerfile must contain 'USER appuser' to run Streamlit as non-root (INFRA-01)."
    )
    assert "useradd -u 1001 -g appgroup -m -d /home/appuser" in DOCKERFILE, (
        "useradd must include '-m -d /home/appuser' so Streamlit can write to ~/.streamlit/ "
        "(Pitfall 3 — without -m, Streamlit fails to start)."
    )


def test_dockerfile_does_not_bake_secrets():
    """Dockerfile must never contain OPENAI_API_KEY or ENV DEMO_MODE= (Threat T-04-06)."""
    assert "OPENAI_API_KEY" not in DOCKERFILE, (
        "OPENAI_API_KEY MUST NOT appear in Dockerfile — it bakes the secret into image layers. "
        "Inject at runtime via compose.yaml env_file: .env (Threat T-04-06)."
    )
    assert not re.search(r"^ENV\s+DEMO_MODE", DOCKERFILE, re.MULTILINE), (
        "ENV DEMO_MODE assignment MUST NOT appear in Dockerfile — mode toggle must come from "
        "compose env_file at runtime, not baked into the image."
    )


def test_compose_app_has_no_published_port():
    """App service must not publish any host ports — Caddy reaches it via internal Docker DNS."""
    assert "ports" not in COMPOSE["services"]["app"], (
        "app service MUST NOT publish ports (Anti-Pattern in RESEARCH.md). "
        "The app is internal-only; Caddy reaches it at app:8501 over the internal bridge network."
    )


def test_compose_uses_named_caddy_volumes():
    """Caddy data and config volumes must be named (not bind mounts) to survive restarts (Pitfall 2)."""
    top_level_volumes = COMPOSE.get("volumes", {})
    assert "caddy_data" in top_level_volumes, (
        "top-level 'volumes' must declare 'caddy_data' as a named volume "
        "(Pitfall 2 — bind mount would lose Let's Encrypt certs on every 'docker compose down')."
    )
    assert "caddy_config" in top_level_volumes, (
        "top-level 'volumes' must declare 'caddy_config' as a named volume "
        "(Pitfall 2 — Caddy autosaved state must persist across restarts)."
    )


def test_caddyfile_has_reverse_proxy_directive():
    """Caddyfile must contain a reverse_proxy directive pointing to app:8501."""
    assert "reverse_proxy app:8501" in CADDYFILE, (
        "caddy/Caddyfile must contain 'reverse_proxy app:8501' to forward traffic "
        "from Caddy to the Streamlit container on the internal Docker network."
    )


def test_streamlit_config_disables_both_cors_and_xsrf():
    """Both CORS and XSRF protection must be disabled under [server] (Pitfall 5).

    Setting only enableCORS=false causes Streamlit to silently re-enable CORS.
    Both flags must be present and under the [server] section (not just anywhere in the file).
    """
    server_match = re.search(r"\[server\](.*?)(\[|\Z)", STREAMLIT_CFG, re.DOTALL)
    assert server_match is not None, "Could not find [server] section in .streamlit/config.toml"
    server_body = server_match.group(1)

    assert "enableCORS = false" in server_body, (
        "enableCORS = false must appear under [server] in .streamlit/config.toml "
        "(Pitfall 5 — required alongside enableXsrfProtection=false for behind-proxy operation)."
    )
    assert "enableXsrfProtection = false" in server_body, (
        "enableXsrfProtection = false must appear under [server] in .streamlit/config.toml "
        "(Pitfall 5 — setting only enableCORS=false silently re-enables CORS)."
    )


def test_dockerignore_excludes_env_and_tests():
    """Critical paths must be excluded from the Docker build context (Threats T-04-06, T-04-11)."""
    assert ".env" in DOCKERIGNORE, (
        ".env must be in .dockerignore so developer secrets never enter image layers via "
        "'COPY . /app' (Threat T-04-06 — OPENAI_API_KEY secret guard)."
    )
    assert "tests/" in DOCKERIGNORE, (
        "tests/ must be in .dockerignore to keep the runtime image lean and prevent test "
        "fixtures from leaking into production layers (Threat T-04-11)."
    )
    assert ".planning/" in DOCKERIGNORE, (
        ".planning/ must be in .dockerignore to prevent planning notes and dev artifacts "
        "from leaking into production image layers (Threat T-04-11)."
    )
