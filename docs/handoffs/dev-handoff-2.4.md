# Handoff: Story 2.4 - Create CI/CD Pipeline

This document is a handoff for the development agent to implement Story 2.4.

## Story Details

- **As a developer, I want to create a basic CI/CD pipeline (using GitHub Actions) that automates testing and builds, so that code quality and integration are maintained.**

## Acceptance Criteria

1.  A GitHub Actions workflow file exists at `.github/workflows/ci.yml`.
2.  The workflow triggers on every push to the `main` branch.
3.  The workflow includes jobs for:
    - Linting and running unit tests.
    - Building the Docker image.
    - (Optional but recommended) Scanning the container image for vulnerabilities.

## Tasks

1.  **Create Workflow Directory**:

    - Create the `.github/workflows` directory if it doesn't exist.

2.  **Create `ci.yml` Workflow File**:

    - Define the workflow name and trigger (`on: push: branches: [ main ]`).

3.  **Define the `lint-and-test` Job**:

    - Uses `ubuntu-latest`.
    - Checks out the code (`actions/checkout@v4`).
    - Sets up Python 3.11.
    - Installs `uv`.
    - Runs unit tests: `uv run pytest`.

4.  **Define the `build` Job**:

    - Uses `ubuntu-latest`.
    - Checks out the code.
    - Logs into a container registry (e.g., Docker Hub). This will require secrets (`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`).
    - Builds and pushes the Docker image using the `Dockerfile` from Story 2.3.
    - The image should be tagged appropriately (e.g., `your-repo/aks-copilot:latest`).

5.  **(Optional) Add a `scan` Job**:
    - After the `build` job, add a step to scan the newly built image for vulnerabilities using a tool like Trivy (`aquasecurity/trivy-action`).

## Secrets

The following secrets will need to be configured in the GitHub repository settings for the workflow to succeed:

- `DOCKERHUB_USERNAME`: Your Docker Hub username.
- `DOCKERHUB_TOKEN`: A Docker Hub access token with write permissions.

## Confirmation

The development agent should confirm once the workflow file is created and successfully runs on a push to `main`.
