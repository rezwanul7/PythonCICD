#!/bin/bash

# Ensure that the script exits immediately if any command it runs exits with a non-zero status.
set -e

# Install dependencies
export PATH=$HOME/.local/bin:$PATH
poetryx install

# Restart the FastAPI app
echo "restarting the app"
systemctl restart python_cicd_app.service

echo "Deployment completed successfully."