# Epic 2 — Story 2.1: Integrate the AI/LLM Service

- As a developer, I want to integrate the agent with an AI/LLM service, so that it can be used for advanced, intelligent patching.

Acceptance Criteria

1. The agent can successfully send a prompt to the configured LLM and receive a response.
2. The LLM endpoint is configurable.

Tasks

- Add configuration for LLM endpoint and API key (environment variables).
- Implement a small adapter to send structured prompts and receive JSON responses.
- Add unit tests mocking the LLM responses.
- Document LLM configuration in `README.md`.
