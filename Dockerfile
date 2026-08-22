# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.9.18@sha256:5713fa8217f92b80223bc83aac7db36ec80a84437dbc0d04bbc659cae030d8c9 AS uv
FROM python:3.12.11-slim-bookworm@sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7

COPY --from=uv /uv /uvx /bin/
RUN useradd --create-home --uid 10001 rci
WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis \
    PYTEST_ADDOPTS="-p no:cacheprovider" \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1

COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --all-extras --dev --no-install-project

COPY --chown=rci:rci . .
RUN uv sync --frozen --all-extras --dev && chown -R rci:rci /workspace/.venv

USER rci
CMD ["uv", "run", "--no-sync", "pytest", "-q", "--basetemp=/tmp/pytest"]
