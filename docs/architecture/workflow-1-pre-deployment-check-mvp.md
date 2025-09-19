# Workflow 1: Pre-Deployment Check (MVP)

The **Thinker** in this workflow is stateless and does not have live access to Azure. It generates patches based on general rules.

```mermaid
sequenceDiagram
    participant CI/CD Pipeline
    participant Inspector
    participant Thinker
    participant Patcher
    participant Reporter

    CI/CD Pipeline->>+Inspector: Run analysis
    Inspector-->>-CI/CD Pipeline: Return violations
    CI/CD Pipeline->>+Thinker: Get patches
    Thinker-->>-CI/CD Pipeline: Return patch operations
    CI/CD Pipeline->>+Patcher: Apply patches
    Patcher-->>-CI/CD Pipeline: Return final manifests
    CI/CD Pipeline->>+Reporter: Deploy and report
```

### Workflow 2: Post-Deployment Debugging (Post-MVP)

The **Thinker** in this workflow is stateful and has live access to run az and kubectl commands to gather context for its patches.

Code snippet

```mermaid
sequenceDiagram
    participant Argo CD
    participant Inspector
    participant Thinker
    participant GitHub API
    participant "Live Azure/AKS"

    Argo CD->>+Inspector: Run debugger (trigger)
    Inspector->>+Live Azure/AKS: Read logs & events
    Live Azure/AKS-->>-Inspector: Return failure data
    Inspector-->>-Argo CD: Return violations

    Argo CD->>+Thinker: Get patches
    Thinker->>+Live Azure/AKS: Get live context (az/kubectl)
    Live Azure/AKS-->>-Thinker: Return context
    Thinker-->>-Argo CD: Return patch operations

    Argo CD->>+GitHub API: Commit patch
```
