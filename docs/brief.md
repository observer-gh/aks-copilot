# Project Brief: aks-copilot

### Executive Summary

Our goal is to build an AI agent called "aks-copilot". It helps move Kubernetes files from a local setup to Azure (AKS). The agent uses a simple "Inspect, Explain, Patch" method to find and fix problems automatically. This saves time and reduces errors for businesses migrating to the cloud.

### Problem Statement

Moving applications to the cloud is a big, important market. However, the process is often complex, manual, and full of errors. A key pain point is that Kubernetes files working on a local machine (like k3s) frequently fail when deployed to Azure (AKS) due to incompatibilities. Existing tools can find these errors, but they don't explain how to fix them for AKS or suggest patches. This leaves developers to solve a tricky problem manually, which causes delays and costs money.

### Proposed Solution

We propose an AI "action agent" called aks-copilot. The agent automates the difficult process of migrating Kubernetes manifests to AKS by following a simple three-step logic: **Inspect -> Explain -> Patch**. What makes it different is that it doesn't just find problems like other tools do. It uses a combination of rule-based checks and AI to explain _why_ something is an issue and then automatically generates a patch to fix it. By fixing these issues _before_ deployment, the tool prevents failures, saves developers significant time, and makes the migration process more reliable.

### Target Users

**Primary User: The DevOps Engineer or Platform-Focused Developer**

- **Who they are:** A skilled engineer responsible for deploying applications to the cloud.
- **Their pain point:** They find the process of migrating Kubernetes files to be complex, manual, and full of errors, which causes project delays and budget overruns.
- **Their goal:** To accelerate the migration process and reduce manual errors, allowing them to focus on more strategic work.

### Goals & Success Metrics

**Business Objectives**

- Accelerate cloud migration project timelines.
- Reduce costs from manual errors and debugging.
- Create a standardized, repeatable migration process.

**User Success Metrics**

- Fewer deployment failures due to configuration errors.
- Less time spent by developers manually fixing manifest files.

**Key Performance Indicators (KPIs)**

- A measurable reduction in the time required for a sample migration project.
- A measurable decrease in the number of manual interventions needed for a successful deployment.

### MVP Scope

**Core Features (Phase 1 - The MVP)**

- The tool will automatically analyze a developer's local Kubernetes manifests when they push to a development branch.
- It must generate a `report.md` detailing any violations, patches, and explanations.
- It must generate a `resources.md` file that lists the required Azure resources.
- It must generate a `patch.json` file with the suggested fixes.
- The main output will be a baseline set of AKS-ready manifest files that the user can then review and apply manually.
- As a final step, it will **attempt to deploy** the patched manifests to a dev/test namespace in AKS.

**Out of Scope for MVP (Phase 2 Features)**

- The complex, iterative **correction loop** (the AI Debugger). The MVP will only try to deploy once. If it fails, it reports the failure and stops.
- Analyzing live cluster logs to diagnose failures.

### Post-MVP Vision

**Phase 2 Features (Immediate Next Steps)**

- The top priority after the MVP is to build the full **AI Debugger**. This includes the automated, iterative correction loop that attempts to fix failed deployments by analyzing live cluster logs and events.

**Expansion Opportunities**

- **Become an Orchestration Agent:** Expand the tool's abilities beyond just fixing manifests. This would include connecting to management APIs (like GitHub and Azure) and executing `kubectl` and `az` commands to provision and check on cloud resources.

### Technical Considerations

**Platform Requirements**

- The final product is an AI agent that runs on **Azure** in a CI/CD pipeline. The specific Azure service (e.g., Container App) will be decided by the Architect.
- A command-line interface (CLI) will be developed as an **internal tool for testing** the agent's logic locally. It is not intended for end-users.

**Architecture Considerations**

- The system **must be configurable** to support different source environments.
- The tool will need to handle secrets safely, using a service like **Azure Key Vault**.

### Constraints & Assumptions

**Constraints (Rules we must follow)**

- The agent is only allowed to modify files within a specific Kubernetes namespace; it cannot change cluster-wide settings.
- The AI Debugger will stop after 5 failed attempts to fix a deployment and will alert a human.
- The agent is forbidden from changing application source code; it can only modify Kubernetes manifest files.
- We must use a cloud vault for managing passwords and other secrets.

**Assumptions (Things we believe to be true)**

- The CI/CD pipeline will use Argo CD, which will provide the success or failure signal to trigger the AI Debugger.
- The necessary Azure cloud infrastructure (like the AKS cluster and Key Vault) will be set up and available for the agent to use.
- We will have access to the internal KT knowledge bases to power the agent's AI (RAG system).
