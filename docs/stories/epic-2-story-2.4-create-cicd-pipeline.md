# Epic 2 — Story 2.4: Create a CI/CD Pipeline for Deployment

- As a developer, I want to create a basic CI/CD pipeline (using GitHub Actions) that attempts to deploy the patched manifests to our test AKS cluster, so that the agent's full workflow can be triggered automatically.

Acceptance Criteria

1. A GitHub Actions workflow file is configured in the repository.
2. When triggered, the workflow builds the container and runs the deployment command against the test AKS cluster.

Tasks

- Add `.github/workflows/deploy.yml` template.
- Configure job to build Docker image and run `copilot fix-folder` against a test fixture.
- Add secrets/inputs documentation for AKS credentials and Slack webhook.
