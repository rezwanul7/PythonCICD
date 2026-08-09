# Stage 1: Build and install dependencies using Poetry
FROM python:3.11 AS builder

ARG BUILD_ENVIRONMENT
RUN echo "BUILD_ENVIRONMENT is $BUILD_ENVIRONMENT"

    # Specify a longer timeout for larger packages or slow network
ENV PYTHONUNBUFFERED=1 \
    # Allow statements and log messages to immediately appear
    PIP_DEFAULT_TIMEOUT=100 \
    # Disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Cache is useless in docker image, so disable to reduce image size
    PIP_NO_CACHE_DIR=1 \
    # Use a specific version of a package manager
    POETRY_VERSION=1.8.2 \
    # Ensure scripts installed in .local are usable
    PATH="/home/appuser/.local/bin:${PATH}"

# Set a non-root user and switch to it
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Copy the required package info files into the container
COPY --chown=appuser:appuser poetry.lock pyproject.toml ./

# Export requirements.txt using poetry and Install dependencies using pip
RUN pip install --user "poetry==$POETRY_VERSION" \
    # Use Poetry to export the dependencies to a requirements.txt file
    && poetry export $(test "$BUILD_ENVIRONMENT" != development && echo "--without dev") --without-hashes --format=requirements.txt > requirements.txt \
    # Install dependencies
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Stage 2: Copy only the necessary artifacts to the final image
FROM python:3.11-slim as final

# Set environment variables
# Allow statements and log messages to immediately appear
ENV PYTHONUNBUFFERED=1 \
    # Ensure scripts installed in .local are usable
    PATH="/home/appuser/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Set a non-root user and switch to it
RUN useradd --create-home appuser
WORKDIR /home/appuser
USER appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Copy the application code [all other files except filtered by .dockerignore]
COPY --chown=appuser:appuser . .

# Expose the port that API will run on
EXPOSE 8000