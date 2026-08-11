#!/usr/bin/env bash

set -euo pipefail

readonly docker_repo="${DOCKER_REPO:?DOCKER_REPO is required}"
readonly production_image="${PRODUCTION_IMAGE:?PRODUCTION_IMAGE is required}"
readonly source_sha="${GITHUB_SHA:?GITHUB_SHA is required}"
readonly branch="${GITHUB_REF_NAME:?GITHUB_REF_NAME is required}"
readonly step_summary="${GITHUB_STEP_SUMMARY:?GITHUB_STEP_SUMMARY is required}"

case "$branch" in
  dev) channel_tag="dev" ;;
  staging) channel_tag="staging" ;;
  main) channel_tag="latest" ;;
  *) echo "Unsupported publishing branch: $branch" >&2; exit 1 ;;
esac

readonly immutable_image="$docker_repo:sha-$source_sha"
readonly channel_image="$docker_repo:$channel_tag"

docker tag "$production_image" "$immutable_image"
docker tag "$production_image" "$channel_image"
docker push "$immutable_image"
docker push "$channel_image"

docker pull "$immutable_image"
repository_digest="$(docker image inspect \
  --format '{{index .RepoDigests 0}}' \
  "$immutable_image")"
image_digest="${repository_digest#*@}"

jq --null-input \
  --arg repository "$docker_repo" \
  --arg digest "$image_digest" \
  --arg immutable_image "$immutable_image" \
  --arg channel_image "$channel_image" \
  --arg source_sha "$source_sha" \
  --arg branch "$branch" \
  '{repository: $repository, digest: $digest, immutable_image: $immutable_image, channel_image: $channel_image, source_sha: $source_sha, branch: $branch}' \
  > release-metadata.json

{
  echo '## Published image'
  echo
  echo "- Immutable image: \`$immutable_image\`"
  echo "- Channel image: \`$channel_image\`"
  echo "- Repository digest: \`$repository_digest\`"
  echo "- Source commit: \`$source_sha\`"
} >> "$step_summary"
