# Stage 1: Build and install dependencies using Poetry
FROM python:3.11 AS builder

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=100 \
    # Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.5.1

COPY pyproject.toml poetry.lock ./
RUN pip install "poetry==$POETRY_VERSION" && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Stage 2: Copy only the necessary artifacts to the final image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy the application code [all other files]
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8081

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]