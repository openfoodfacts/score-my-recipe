ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.11.32
ARG USER_UID=1000
ARG USER_GID=1000
ARG UVICORN_NUM_WORKERS_DEFAULT=4

# base python setup
# -----------------
FROM python:${PYTHON_VERSION}-slim AS python-base
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends -y curl && \
    apt-get autoremove --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_CACHE_DIR=/var/cache/uv \
    UV_PYTHON_DOWNLOADS=0
# create off user
ARG USER_UID
ARG USER_GID
RUN groupadd -g $USER_GID off && \
    useradd -u $USER_UID -g off -m off && \
    mkdir -p /var/cache/uv && \
    chown off:off /var/cache/uv && \
    mkdir -p /app/data && \
    chown off:off -R /app
# no need to be root for the rest of the build
USER off:off
WORKDIR /app

# Getting uv binaries (because we can't use ARG in COPY --from)
FROM ghcr.io/astral-sh/uv:${UV_VERSION} as uv-image

# building packages
# -----------------
FROM python-base AS builder-base

# add uv
COPY --from=uv-image /uv /uvx /bin/

COPY --chown=off:off pyproject.toml uv.lock /app/
# Install dependencies (bind mounting pyproject.toml and uv.lock)
RUN --mount=type=cache,target=/var/lib/cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
COPY --chown=off:off api /app/api

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# This is our final image
# ------------------------
FROM python-base AS runtime
COPY --from=builder-base /app/ /app/
ENV PATH="/app/.venv/bin:$PATH"
# setting num workers using env variable allows for easy override in docker-compose or k8s
ARG UVICORN_NUM_WORKERS_DEFAULT
ENV UVICORN_WORKERS=${UVICORN_NUM_WORKERS_DEFAULT}
CMD ["uvicorn", "api.api:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]