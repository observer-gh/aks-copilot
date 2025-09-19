# Epic 2 — Story 2.3: Build a Container Image for the Agent

- As a developer, I want to create a `Dockerfile` to package the agent into a container image, so that it can be run in any CI/CD pipeline.

Acceptance Criteria

1. A `Dockerfile` exists in the repository.
2. The `docker build` command successfully creates a runnable container image of the agent.

Tasks

- Create `Dockerfile` with minimal base (python:3.11-slim).
- Add build steps to install dependencies from `pyproject.toml`.
- Add a small `entrypoint.sh` to run the CLI.
- Add test to run `docker build` in CI (optional local validation).
