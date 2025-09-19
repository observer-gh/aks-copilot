# Epic 1 — Story 1.2: Implement the Inspect Engine for a Single Rule

- As a developer, I want the agent to inspect manifest files for a single, simple rule (like incorrect `storageClassName`), so that I can verify the core analysis logic is working.

Acceptance Criteria

1. The agent correctly identifies manifests that violate the `storageClassName` rule.
2. The violations are stored in memory for the next steps.

Tasks

- Implement parser to read Kubernetes YAML manifests (support multi-doc files).
- Implement the `storageClassName` rule checker.
- Store violations in an in-memory structure and provide a small API to access them.
- Add unit tests covering positive and negative cases.

Notes

- Keep rule implementation modular to allow adding more rules later.
