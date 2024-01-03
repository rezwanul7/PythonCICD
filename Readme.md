# PythonCICD
Simple Python Fast API Restful Application CI/CD.

- **poetry** dependency management tool for python
- **fast api** web framework for building APIs

This is the branch for non containerized app CI/CD workflow.

## CI/CD workflow
- [x] Create github actions workflow file
- [x] Create CI Pipeline
- [x] Create CD Pipeline
- [x] Setup Deployment Server
  - [x] Generate Public Private Key
  - [x] Install necessary software packages
  - [x] Create a Systemd Service File
  - [x] Create a Deployment Script
- [x] Setup Github Secrets & Variables to connect to the deployment server using SSH
  - [x] Create HOST = "YOUR SERVER ADDRESS, example: 172.41.91.123"
  - [x] Create USERNAME = "YOUR SERVER USERNAME, example: daniel"
  - [x] Create PRIVATE_KEY = "Copy generated private key from vps to github secret"
- [x] Configure your firewall rules to allow or block specific ports.