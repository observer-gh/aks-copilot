# Epic 1 — Story 1.4: Implement the Patch Engine & `patch.json` Generation

- As a developer, I want the agent to generate a `patch.json` file with the correct fixes for the identified violations, so that the core patching mechanism is in place.

Acceptance Criteria

1. After the agent runs, a `patch.json` file is created.
2. The file contains a valid JSON Patch operation to fix the `storageClassName` violation.

Tasks

- Implement patch generator that creates JSON Patch operations for identified violations.
- Ensure patch format is compatible with `jsonpatch` style operations.
- Provide a dry-run mode that shows patches without applying them.
- Add unit tests to validate patch generation for sample violations.
