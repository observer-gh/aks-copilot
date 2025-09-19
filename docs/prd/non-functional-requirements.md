# Non-Functional Requirements

**NFR1:** The process must be highly automated to reduce manual effort from developers.

**NFR2:** The agent must operate securely, fetching secrets from a cloud service like Azure Key Vault.

**NFR3:** The agent's actions must be strictly limited to a specific namespace; it cannot change cluster-wide configurations.

**NFR4:** The agent must only modify Kubernetes manifest files and is forbidden from changing application source code.

**NFR5:** The agent should prioritize simple, rule-based fixes for known issues before using AI for more complex problems.
