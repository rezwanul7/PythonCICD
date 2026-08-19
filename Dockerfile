# syntax=docker/dockerfile:1

# Build dependencies in a full Debian image so native extensions can compile.
FROM python:3.11.15-bookworm AS builder

ARG BUILD_ENVIRONMENT=production
ARG POETRY_VERSION=1.8.2

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv

# Poetry is installed outside the application virtual environment and remains
# in this disposable stage.
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install "poetry==$POETRY_VERSION" \
    && python -m venv "$VIRTUAL_ENV"

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build

# Dependency metadata is copied before application code to preserve this layer
# when only the application changes.
COPY poetry.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$BUILD_ENVIRONMENT" = "development" ]; then \
        poetry export --with dev --without-hashes --format=requirements.txt --output=/tmp/requirements.txt; \
    else \
        poetry export --without dev --without-hashes --format=requirements.txt --output=/tmp/requirements.txt; \
    fi \
    && python -m pip install --requirement /tmp/requirements.txt

# Run the application from a smaller image with no build tooling or Poetry.
FROM python:3.11.15-slim-bookworm AS final

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home --no-log-init appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /home/appuser

# Application and static files remain root-owned and read-only. The uploads
# directory is writable so it has the same contract with or without a volume.
COPY . .
RUN chown --recursive appuser:appuser uploads \
    && chmod 0750 uploads \
    && chmod 0640 uploads/demo.txt

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
