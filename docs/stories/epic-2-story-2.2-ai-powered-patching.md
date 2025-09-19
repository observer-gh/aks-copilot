# Epic 2 — Story 2.2: Implement AI-Powered Patching for a Complex Rule

- As a developer, I want the agent to use the LLM to suggest patches for a complex issue that the rules engine cannot handle (e.g., adding specific Ingress annotations), so that we can validate the AI patching workflow.

Acceptance Criteria

1. When a complex Ingress issue is detected, the agent sends a structured prompt to the LLM.
2. The agent correctly processes the LLM's response and adds the suggested patch to the `patch.json` file.

Tasks

- Design prompt template for Ingress annotation fixes.
- Implement LLM adapter usage in the patch pipeline.
- Validate and sanitize LLM responses before adding to `patch.json`.
- Add tests with mocked LLM replies.
