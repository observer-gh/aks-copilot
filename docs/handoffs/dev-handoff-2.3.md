# Handoff: Story 2.3 - Build a Container Image for the Agent

This document is a handoff for the development agent to implement Story 2.3.

## Story Details

- **As a developer, I want to create a `Dockerfile` to package the agent into a container image, so that it can be run in any CI/CD pipeline.**

## Acceptance Criteria

1.  A `Dockerfile` exists in the root of the repository.
2.  The `docker build . -t aks-copilot:latest` command successfully creates a runnable container image of the agent.
3.  The container can be run and can execute the `copilot --help` command.

## Tasks

1.  **Create `Dockerfile`**:

    - Use a minimal base image like `python:3.11-slim`.
    - Set up a non-root user for security.
    - Copy the entire project source into the container.
    - Install dependencies using `uv` from `pyproject.toml`.
    - Set the `WORKDIR` to the project root.

2.  **Create `entrypoint.sh`**:

    - Create a simple shell script at `.docker/entrypoint.sh`.
    - This script should activate the virtual environment (if any) and then execute the `copilot` command passed as arguments (`$@`).
    - Ensure the script is executable (`chmod +x`).

3.  **Update `.dockerignore`**:
    - Create a `.dockerignore` file to exclude unnecessary files and directories from the build context (e.g., `.git`, `__pycache__`, `.venv`, `*.pyc`, `docs/`).

## Confirmation

The development agent should confirm once all tasks are completed and the acceptance criteria are met.
