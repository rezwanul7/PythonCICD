#!/bin/bash
# Install dependencies
export PATH=$HOME/.local/bin:$PATH
poetry install

# Restart the FastAPI app
echo "restarting the app"
systemctl restart python_cicd_app.service