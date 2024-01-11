# PythonCICD
Simple Python Fast API Restful Application CI/CD.

- **poetry** dependency management tool for python
- **fast api** web framework for building APIs

This is the branch for containerized app CI/CD workflow.

## CI/CD workflow
- [x] Create github actions workflow file
- [x] Create CI Pipeline
- [x] Create CD pipeline with docker push pull
- [x] Deployment Server Setup
  - [x] Generate Public Private Key
  - [x] Install necessary software packages
- [x] Setup Github Secrets & Variables to connect to the deployment server using SSH
  - [x] Create HOST = "YOUR SERVER ADDRESS, example: 172.41.91.123"
  - [x] Create USERNAME = "YOUR SERVER USERNAME, example: daniel"
  - [x] Create PRIVATE_KEY = "Copy generated private key from vps to github secret"


## Docker Compose
For local development: 
```shell
docker compose -f common.yaml -f compose.dev.yaml config
docker compose -f common.yaml -f compose.dev.yaml up -d
```

App will be running at 

For staging: 
```shell
docker compose -f common.yaml -f compose.stag.yaml config
docker compose -f common.yaml -f compose.stag.yaml pull
docker compose -f common.yaml -f compose.stag.yaml up -d
```