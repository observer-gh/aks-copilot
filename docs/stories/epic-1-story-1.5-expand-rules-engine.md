# Epic 1 — Story 1.5: Expand the Rules Engine with All MVP Rules

- As a developer, I want to add the remaining rule-based checks (e.g., for missing resource limits), so that the agent can handle all planned, predictable issues for the MVP.

Acceptance Criteria

1. The agent can now find and fix all the simple, rule-based issues defined in our MVP scope.
2. The `report.md` and `patch.json` files are correctly generated for all identified rule-based violations.

Tasks

- Enumerate MVP rules and implement each as a modular rule.
- Add integration tests covering multiple-rule detection and patching.
- Update documentation listing all supported rules.
