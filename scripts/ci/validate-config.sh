#!/usr/bin/env bash

set -euo pipefail

readonly compose_base="docker/docker-compose.yaml"
readonly rendered_manifest=".tmp/k8s/production.yaml"

docker build --check .

for environment in dev staging prod; do
  docker compose \
    --file "$compose_base" \
    --file "docker/docker-compose.${environment}.yaml" \
    config --quiet
done

mkdir -p "$(dirname "$rendered_manifest")"
: > "$rendered_manifest"

for manifest in k8s/production/*.yaml; do
  printf '%s\n' '---' >> "$rendered_manifest"
  cat "$manifest" >> "$rendered_manifest"
done
