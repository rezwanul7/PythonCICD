# PythonCICD Architecture

This document describes the architecture that exists in the repository today.
It is a living document: update it when a component, deployment boundary, or
operational responsibility changes. Planned capabilities are listed separately
and must not be interpreted as already implemented.

## Current status

PythonCICD is a small, stateless FastAPI service packaged as a Docker image. It
can run locally with Docker Compose and in production on Kubernetes. GitHub
Actions validates the application and publishes images to Docker Hub, while the
Kubernetes deployment is performed manually from a trusted workstation.

The current system does not include a database, message broker, persistent
storage, public ingress, DNS, TLS automation, or an external secrets manager.

## System context

```mermaid
flowchart LR
    User[API consumer] -->|HTTP| Entry[Local port forward or internal cluster client]
    Entry --> Service[Kubernetes ClusterIP Service]
    Service --> PodA[FastAPI Pod]
    Service --> PodB[FastAPI Pod]

    Developer[Developer] -->|push| GitHub[GitHub repository]
    GitHub -->|workflow| Actions[GitHub Actions]
    Actions -->|push image| DockerHub[Docker Hub]
    Operator[Operator] -->|kubectl apply| Cluster[Kubernetes cluster]
    DockerHub -->|pull immutable image| PodA
    DockerHub -->|pull immutable image| PodB
    Cluster --- Service
```

There are two distinct paths:

- The **request path** sends HTTP traffic through the Kubernetes Service to one
  of the application Pods.
- The **delivery path** tests and publishes an image in CI, then relies on an
  operator to select that image and apply the Kubernetes manifests.

GitHub-hosted runners do not have access to the Kubernetes cluster and do not
deploy the application.

## Application architecture

The application is a single Python process running FastAPI through Uvicorn on
port `8000`.

```text
src/main.py
  |-- application lifespan and state
  |-- GET /
  |-- /public static files
  |-- health router
  `-- items router
```

The application currently provides:

- `GET /` for application metadata and the active environment.
- `GET /items/{item_id}` as an example API endpoint.
- `GET /health/startup`, `/health/live`, and `/health/ready` for Kubernetes
  probes.
- `/public` for static files bundled into the image.
- `/docs` for the FastAPI-generated OpenAPI interface.

Application state is process-local and ephemeral. Any Pod can serve any
request, and a Pod can be replaced without data migration or recovery. This is
what allows the Deployment to run multiple interchangeable replicas.

## Container architecture

The `Dockerfile` uses a multi-stage build:

1. The builder stage installs Poetry, exports dependencies, and installs them
   into `/opt/venv`.
2. The final stage copies only the virtual environment and application files
   into a smaller Python image.
3. The process runs as the unprivileged `appuser` user with UID and GID `10001`.
4. Uvicorn listens on `0.0.0.0:8000`.

The production image excludes Poetry, pytest, and other development-only
dependencies. Application and static files are included in the image, so a new
image is required for every code or static-content release.

## Runtime environments

| Environment             | Runtime                                      | Exposure                     | Configuration                       |
|-------------------------|----------------------------------------------|------------------------------|-------------------------------------|
| Native development      | Poetry and Uvicorn                           | `localhost:8000`             | Local environment                   |
| Docker development      | Docker Compose with source mounts and reload | `localhost:5051`             | `APP_ENV=development`               |
| Docker staging check    | Docker Compose and published image           | `localhost:8001`             | `APP_ENV=staging`                   |
| Docker production check | Docker Compose and published image           | `localhost:8000`             | `APP_ENV=production`                |
| Kubernetes production   | Two Pods behind a ClusterIP Service          | Cluster-internal port `8000` | ConfigMap with `APP_ENV=production` |

Docker Compose is a local runtime convenience; it is not part of the
Kubernetes production topology.

## Kubernetes topology

The production manifests under `k8s/production` create three resources in the
current namespace:

| Resource   | Name          | Responsibility                                                  |
|------------|---------------|-----------------------------------------------------------------|
| ConfigMap  | `python-cicd` | Supplies non-sensitive application configuration                |
| Deployment | `python-cicd` | Maintains two application replicas and performs rolling updates |
| Service    | `python-cicd` | Provides stable, internal routing to ready Pods                 |

The Deployment uses the label `app.kubernetes.io/name: python-cicd` to connect
the Deployment selector, Pod labels, and Service selector.

### Availability and lifecycle

- Two replicas provide process-level redundancy.
- Rolling updates allow one additional Pod and require existing replicas to
  remain available (`maxSurge: 1`, `maxUnavailable: 0`).
- The startup probe gives the process time to initialize.
- The readiness probe controls whether a Pod receives Service traffic.
- The liveness probe asks Kubernetes to restart a process that stops responding.
- A 30-second termination grace period permits orderly shutdown.

This improves availability within one cluster but does not provide
multi-cluster or multi-region disaster recovery.

### Resources and storage

Each Pod requests `100m` CPU and `128Mi` memory and is limited to `500m` CPU and
`256Mi` memory. With two replicas, the scheduler needs at least `200m` CPU and
`256Mi` memory for the requested application capacity, excluding platform
overhead.

The container root filesystem is read-only. A temporary `emptyDir` volume is
mounted at `/tmp`; its contents disappear when the Pod is replaced. There are
no PersistentVolumes.

### Network exposure

The Service type is `ClusterIP`. The API is therefore reachable only from
inside the cluster or through an operator-established `kubectl port-forward`.
There is currently no public production endpoint.

## Configuration and secrets

`APP_ENV` is the only application configuration currently supplied by
Kubernetes. It is non-sensitive and stored in a ConfigMap.

Docker Hub credentials are GitHub Actions secrets and are used only to publish
images. No runtime application secrets are required. If the image repository
becomes private, the cluster will also need a registry credential referenced by
the Pod through `imagePullSecrets`.

Sensitive values must not be added to the ConfigMap or committed to manifests.
A Kubernetes Secret or external secrets system should be introduced before the
application needs credentials.

## Delivery architecture

The workflow in `.github/workflows/python-app-ci-cd-docker.yml` runs for pull
requests and pushes involving `dev`, `staging`, or `main`, except
documentation-only changes. Only pushes publish images. The branch channel
mapping is `dev` to `dev`, `staging` to `staging`, and `main` to `latest`.

```mermaid
flowchart LR
    Change[Pull request or push] --> Tests[Tests and Ruff checks]
    Tests --> Validation[Docker and Kubernetes validation]
    Validation --> ImageTests[Production and development image tests]
    ImageTests --> Event{Push?}
    Event -->|No| Complete[CI complete]
    Event -->|Yes| Publish[Tag and publish tested image]
    Publish --> Channel[dev, staging, or latest tag]
    Publish --> Immutable[sha-full-git-sha tag and digest metadata]
    Immutable --> Select[Operator selects tag]
    Select --> Apply[kubectl apply]
    Apply --> Rollout[Kubernetes rolling update]
```

CI separates its responsibilities into three jobs:

- `quality` runs Python tests, linting, and formatting checks.
- `configuration` validates the Dockerfile, all Compose configurations, and the
  offline Kubernetes schema.
- `image` builds and tests the production and development images. On pushes it
  publishes the exact tested production image and its release metadata.

The detailed configuration, image-test, and publishing commands live in focused
scripts under `scripts/ci/`. The `image` job depends on both preceding jobs, so
publishing cannot begin unless every validation succeeds.

Pull requests do not receive Docker Hub credentials and cannot publish images.
Per-branch concurrency prevents older in-progress workflows from replacing a
newer channel tag.

Kubernetes production should use the immutable SHA tag published from `main`.
The operator records the selected version in `k8s/production/deployment.yaml`,
reviews the change, and applies it manually. The complete procedure is in the
[Kubernetes deployment runbook](kubernetes-deployment-runbook.md).

## Security posture

The current runtime applies these controls:

- The container runs as a fixed non-root user.
- Privilege escalation is disabled.
- Linux capabilities are dropped.
- The default runtime seccomp profile is enabled.
- The root filesystem is read-only.
- CPU and memory limits constrain resource consumption.
- The Service is not publicly exposed.

Current limitations include:

- Images are identified by immutable tags but are not pinned by digest.
- No image signing, provenance verification, or vulnerability-scanning policy
  is enforced by the cluster.
- Kubernetes RBAC, namespace policy, NetworkPolicy, and Pod security admission
  are managed outside this repository and are not documented yet.
- There is no application authentication or authorization layer.

## Observability and operations

The application writes logs to the container's standard output and error
streams. Operators can inspect them with `kubectl logs`. Kubernetes uses the
three HTTP health endpoints for lifecycle management.

There is currently no centralized log aggregation, metrics endpoint, tracing,
alerting, dashboard, or service-level objective. Operational diagnosis relies
on Pod logs, resource status, and Kubernetes events as described in the
deployment runbook.

## Known boundaries

- The service is stateless and has no external data dependencies.
- The production deployment targets one Kubernetes cluster and the current
  kubectl namespace.
- Releases require a manual manifest update and `kubectl apply`.
- Rollback uses Kubernetes rollout history and must be reconciled back into the
  manifest afterward.
- Scaling is fixed at two replicas; no HorizontalPodAutoscaler is configured.
- Public networking and certificate management are intentionally out of scope
  for the current basic setup.

## Evolution backlog

The next architecture changes should be documented when their requirements are
known. Likely additions are:

1. Introduce a namespace and environment-specific configuration strategy.
2. Add Ingress or Gateway, DNS, and TLS for controlled public access.
3. Add centralized metrics, logs, dashboards, and alerts.
4. Add runtime secrets management when the first sensitive dependency appears.
5. Add NetworkPolicy and document cluster RBAC and Pod security requirements.
6. Automate deployment promotion after the manual process is well understood.
7. Add autoscaling only after real resource and traffic measurements exist.
8. Define backup and disaster-recovery behavior when persistent data is added.

These are candidates, not commitments. Each addition should be driven by an
explicit requirement and captured in this document or in a separate
Architecture Decision Record when it introduces a meaningful trade-off.
Kubernetes environment isolation and automated digest promotion are explicitly
deferred to Phase 2; the Docker and CI foundation does not change the current
Kubernetes topology.

## Keeping this document current

Update this document in the same change that alters any of the following:

- Runtime components or external dependencies.
- Network boundaries or public exposure.
- Configuration, secrets, storage, or data ownership.
- Build, release, deployment, or rollback responsibilities.
- Availability, scaling, security, or observability controls.

Keep statements about the current system factual. Move completed items out of
the evolution backlog, and record significant design decisions under
`docs/decisions/` if Architecture Decision Records are introduced later.
