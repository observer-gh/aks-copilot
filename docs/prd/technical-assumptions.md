# Technical Assumptions

**Repository Structure: Standalone Repository**

- The `aks-copilot` will be developed in its own dedicated Git repository. This is the simplest approach for a self-contained tool.

**Service Architecture: Event-Driven / Serverless**

- The agent is designed to run in response to triggers (like a Git push or an Argo CD signal). A serverless or event-driven architecture is a natural fit for this model, as it's efficient and scalable.

**Testing Requirements: Unit & Integration Testing**

- The agent's core logic for analyzing and patching files must be covered by a strong suite of unit and integration tests to ensure its actions are reliable and correct.
