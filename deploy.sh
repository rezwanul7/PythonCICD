#!/bin/bash
# Go to your app directory
cd ~/PythonCICD

# Pull the latest code
git pull origin develop
git checkout develop
git status

# Install dependencies
poetry install

# Restart the FastAPI app
systemctl restart python_cicd_app.service