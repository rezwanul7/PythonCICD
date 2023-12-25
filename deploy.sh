#!/bin/bash
# Install dependencies
poetry install

# Restart the FastAPI app
systemctl restart python_cicd_app.service