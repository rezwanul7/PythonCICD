# Stage 1: Build and install dependencies using Poetry
FROM python:3.11 AS builder

WORKDIR /app

ARG BUILD_ENVIRONMENT=production
RUN echo "BUILD_ENVIRONMENT is $BUILD_ENVIRONMENT"

    # Specify a longer timeout for larger packages or slow network
ENV PYTHONUNBUFFERED=1 \
    # Allow statements and log messages to immediately appear
    PIP_DEFAULT_TIMEOUT=100 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # cache is useless in docker image, so disable to reduce image size
    PIP_NO_CACHE_DIR=1 \
    # use a specific version of a package manager
    POETRY_VERSION=1.5.1

# System dependencies: Install dependency manager
RUN pip install "poetry==$POETRY_VERSION"

# Install app dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry export $(test "$BUILD_ENVIRONMENT" != production && echo "--with dev") --without-hashes --format=requirements.txt > requirements.txt


# Stage 2: Copy only the necessary artifacts to the final image
FROM python:3.11-slim as final

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN set -ex \
    # Create a non-root user
    && addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 --no-create-home appuser \
    # Upgrade the package index and install security upgrades
    && apt-get update \
    && apt-get upgrade -y \
    # Install dependencies
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code [all other files]
COPY . .

# Set ownership to specific folders for appuser:appgroup
RUN chown -R appuser:appgroup ./public

# Set the user to run the application
USER appuser

# Expose the port that FastAPI will run on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
