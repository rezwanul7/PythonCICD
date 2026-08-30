# Self-hosted private registry CI setup

The `FastShip Docker Build - Self-Hosted Test` GitHub Actions workflow runs
when a non-documentation change is pushed to `test-self-hosted`. It uses a
Linux x64 self-hosted runner, tests the application and its images, logs in to
the private registry, and publishes:

- `registry.marsadlab.com/rezwanul7/fastship-app:test`
- `registry.marsadlab.com/rezwanul7/fastship-app:sha-<full-git-sha>`

The workflow definition is
`.github/workflows/fastship-app-ci-cd-docker-test.yml`.

## 1. Check the self-hosted runner

Open the repository in GitHub and go to **Settings > Actions > Runners**. The
runner must be online and have all three labels required by the workflow:

- `self-hosted`
- `linux`
- `x64`

The runner also needs the following commands available to its service account:

```bash
docker version
docker compose version
bash --version
curl --version
jq --version
```

That account must have permission to use the Docker daemon. GitHub Actions also
downloads the actions and container images referenced by the workflow, so the
runner needs outbound access to GitHub, GitHub Container Registry, and the
Python package sources used by Poetry.

The registry must present a TLS certificate trusted by the runner. Because the
registry is now secured, remove any old `registry.marsadlab.com` or
`148.230.123.192:5000` entry from Docker's `insecure-registries` configuration
and restart Docker.

Check registry reachability from the runner:

```bash
curl -i https://registry.marsadlab.com/v2/
docker login registry.marsadlab.com --username marsad
```

An unauthenticated request to `/v2/` should return `401 Unauthorized`. The
interactive Docker login should succeed with the registry password. Do not put
the password directly in a shell command or commit it to this repository.

## 2. Create the GitHub Actions variables

In GitHub, go to **Settings > Secrets and variables > Actions > Variables**.
Create these repository variables:

| Name | Value |
|------|-------|
| `PRIVATE_REGISTRY_HOST` | `registry.marsadlab.com` |
| `PRIVATE_REGISTRY_REPOSITORY` | `rezwanul7/fastship-app` |

Use only the registry hostname for `PRIVATE_REGISTRY_HOST`: do not include
`https://` or a trailing slash. The workflow combines the two variables into
`registry.marsadlab.com/rezwanul7/fastship-app`.

## 3. Create the GitHub Actions secrets

Go to **Settings > Secrets and variables > Actions > Secrets**. Create these
repository secrets:

| Name | Value |
|------|-------|
| `PRIVATE_REGISTRY_USERNAME` | `marsad` |
| `PRIVATE_REGISTRY_PASSWORD` | The password for the `marsad` registry account |

The names must match exactly. Keep both credentials in GitHub Actions secrets;
do not add them as variables, workflow text, or repository files.

## 4. Trigger and verify the workflow

Push a commit containing at least one non-Markdown change:

```bash
git switch test-self-hosted
git push origin test-self-hosted
```

Documentation-only pushes are ignored by this workflow. In GitHub, open
**Actions > FastShip Docker Build - Self-Hosted Test** and confirm that these
jobs pass:

1. `Python Quality`
2. `Configuration Validation`
3. `Image Test & Publish`

The final job should complete `Login to private registry`, publish the `test`
and immutable SHA tags, and upload a release metadata artifact. Verify the
published test tag from an authorized Docker client:

```bash
docker login registry.marsadlab.com --username marsad
docker pull registry.marsadlab.com/rezwanul7/fastship-app:test
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Workflow remains queued | Confirm the runner is online and has `self-hosted`, `linux`, and `x64` labels. |
| `unauthorized` during login | Re-enter both GitHub secrets and confirm the registry account is enabled. |
| `denied: requested access` during push | Confirm `marsad` has push access to `rezwanul7/fastship-app`. |
| `x509: certificate signed by unknown authority` | Install the registry CA on the runner or fix the registry certificate chain. Do not fall back to an insecure registry. |
| `server gave HTTP response to HTTPS client` | Confirm the registry serves HTTPS and that `PRIVATE_REGISTRY_HOST` is exactly `registry.marsadlab.com`. |
| Registry variables reported missing | Check that both entries were created as repository **variables**, not secrets. |
