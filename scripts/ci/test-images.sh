#!/usr/bin/env bash

set -euo pipefail

readonly production_image="${PRODUCTION_IMAGE:?PRODUCTION_IMAGE is required}"
readonly development_image="fastship-app:ci-development"
container_id=""
host_port=""

cleanup() {
  if [[ -n "$container_id" ]]; then
    docker rm --force "$container_id" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

docker build --tag "$production_image" .
docker run --rm "$production_image" sh -c \
  'test "$(id -un)" = appuser && test "$(id -u)" = 10001'
docker run --rm "$production_image" python -c \
  "import importlib.util; import fastapi, uvicorn; assert importlib.util.find_spec('poetry') is None; assert importlib.util.find_spec('pytest') is None"

for environment in staging production; do
  container_id="$(docker run --detach \
    --env APP_ENV="$environment" \
    --publish 127.0.0.1::8000 \
    "$production_image")"
  host_port="$(docker inspect \
    --format '{{(index (index .NetworkSettings.Ports "8000/tcp") 0).HostPort}}' \
    "$container_id")"

  for probe in startup live ready; do
    curl --fail --silent --show-error --retry 10 --retry-delay 2 \
      --retry-connrefused --retry-all-errors \
      --output /dev/null \
      "http://127.0.0.1:$host_port/health/$probe"
  done

  curl --fail --silent --show-error "http://127.0.0.1:$host_port/" \
    | docker exec --interactive "$container_id" python -c \
      'import json, sys; assert json.load(sys.stdin)["environment"] == sys.argv[1]' \
      "$environment"

  docker rm --force "$container_id" >/dev/null
  container_id=""
  host_port=""
done

docker build \
  --build-arg BUILD_ENVIRONMENT=development \
  --tag "$development_image" .
docker run --rm "$development_image" python -m pytest -v
