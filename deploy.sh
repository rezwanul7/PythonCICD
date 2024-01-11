#!/bin/bash

docker compose -f common.yaml -f compose.stag.yaml config
docker compose -f common.yaml -f compose.stag.yaml pull
docker compose -f common.yaml -f compose.stag.yaml up -d
echo "Deployment completed successfully."
