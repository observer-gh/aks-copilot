# aks-copilot Product Requirements Document (PRD)

## Goals and Background Context

**Goals**

- Accelerate cloud migration project timelines.
- Reduce costs from manual errors and debugging.
- Create a standardized, repeatable migration process.

**Background Context**

- A key pain point for developers is that Kubernetes files working on a local machine often fail when deployed to Azure (AKS) due to incompatibilities. Existing tools find these errors but don't suggest the specific fixes needed for AKS, forcing a slow and manual debugging process.

**Change Log**
| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-09-18 | 1.0 | Initial PRD draft | John (PM) |

---

## Functional Requirements

**FR1:** The agent must analyze local Kubernetes manifest files to find configurations that are incompatible with AKS.

**FR2:** It must generate a `report.md` that details all violations, provides a clear explanation for why each change is necessary, and shows the patches it created.

**FR3:** It must generate a `resources.md` file listing the required Azure resources.

**FR4:** It must produce a set of patched, AKS-ready manifest files.

**FR5:** The user must be able to review and manually edit the generated manifests before the deployment attempt.

**FR6:** As part of the MVP, it must attempt a one-time deployment of the patched manifests to a target AKS namespace.

---

## Non-Functional Requirements

**NFR1:** The process must be highly automated to reduce manual effort from developers.

**NFR2:** The agent must operate securely, fetching secrets from a cloud service like Azure Key Vault.

**NFR3:** The agent's actions must be strictly limited to a specific namespace; it cannot change cluster-wide configurations.

**NFR4:** The agent must only modify Kubernetes manifest files and is forbidden from changing application source code.

**NFR5:** The agent should prioritize simple, rule-based fixes for known issues before using AI for more complex problems.

## Technical Assumptions

**Repository Structure: Standalone Repository**

- The `aks-copilot` will be developed in its own dedicated Git repository. This is the simplest approach for a self-contained tool.

**Service Architecture: Event-Driven / Serverless**

- The agent is designed to run in response to triggers (like a Git push or an Argo CD signal). A serverless or event-driven architecture is a natural fit for this model, as it's efficient and scalable.

**Testing Requirements: Unit & Integration Testing**

- The agent's core logic for analyzing and patching files must be covered by a strong suite of unit and integration tests to ensure its actions are reliable and correct.

## Epic List

- **Epic 1: Rule-Based Manifest Analysis & Patching.**

  - **Goal:** Establish the project foundation and deliver a working agent that can find and fix common, **rule-based** incompatibilities, producing both a `report.md` and a `patch.json`.

- **Epic 2: AI-Powered Patching & Deployment Integration.**
  - **Goal:** Enhance the agent with **AI-powered (LLM)** patching for more complex issues, integrate it into a CI/CD pipeline, and enable the one-time deployment attempt to AKS.

## Epic 1 Details: Rule-Based Manifest Analysis & Patching

- **Story 1.1: Project Setup & CLI Foundation**

  - **As a** developer, **I want** to set up the basic Python project structure and a working CLI command, **so that** I have a foundation to build the agent's logic on.
  - **Acceptance Criteria:**
    1. A new Python project is initialized.
    2. A basic CLI command (e.g., `copilot fix-folder <directory>`) exists and can successfully find all `.yml` files in a given directory.

- **Story 1.2: Implement the "Inspect" Engine for a Single Rule**

  - **As a** developer, **I want** the agent to inspect manifest files for a single, simple rule (like incorrect `storageClassName`), **so that** I can verify the core analysis logic is working.
  - **Acceptance Criteria:**
    1. The agent correctly identifies manifests that violate the `storageClassName` rule.
    2. The violations are stored in memory for the next steps.

- **Story 1.3: Implement the "Explain" Engine & Report Generation**

  - **As a** developer, **I want** the agent to generate a `report.md` file that explains the violations it found, **so that** users can understand the issues.
  - **Acceptance Criteria:**
    1. After the agent runs, a `report.md` file is created.
    2. The report correctly lists the `storageClassName` violations found in the previous story, including a clear explanation for each.

- **Story 1.4: Implement the "Patch" Engine & `patch.json` Generation**

  - **As a** developer, **I want** the agent to generate a `patch.json` file with the correct fixes for the identified violations, **so that** the core patching mechanism is in place.
  - **Acceptance Criteria:**
    1. After the agent runs, a `patch.json` file is created.
    2. The file contains a valid JSON Patch operation to fix the `storageClassName` violation.

- **Story 1.5: Expand the Rules Engine with All MVP Rules**
  - **As a** developer, **I want** to add the remaining rule-based checks (e.g., for missing resource limits), **so that** the agent can handle all planned, predictable issues for the MVP.
  - **Acceptance Criteria:**
    1. The agent can now find and fix all the simple, rule-based issues defined in our MVP scope.
    2. The `report.md` and `patch.json` files are correctly generated for all identified rule-based violations.

## Epic 2 Details: AI-Powered Patching & Deployment Integration

- **Story 2.1: Integrate the AI/LLM Service**

  - **As a** developer, **I want** to integrate the agent with an AI/LLM service, **so that** it can be used for advanced, intelligent patching.
  - **Acceptance Criteria:**
    1. The agent can successfully send a prompt to the configured LLM and receive a response.
    2. The LLM endpoint is configurable.

- **Story 2.2: Implement AI-Powered Patching for a Complex Rule**

  - **As a** developer, **I want** the agent to use the LLM to suggest patches for a complex issue that the rules engine cannot handle (e.g., adding specific Ingress annotations), **so that** we can validate the AI patching workflow.
  - **Acceptance Criteria:**
    1. When a complex Ingress issue is detected, the agent sends a structured prompt to the LLM.
    2. The agent correctly processes the LLM's response and adds the suggested patch to the `patch.json` file.

- **Story 2.3: Build a Container Image for the Agent**

  - **As a** developer, **I want** to create a `Dockerfile` to package the agent into a container image, **so that** it can be run in any CI/CD pipeline.
  - **Acceptance Criteria:**
    1. A `Dockerfile` exists in the repository.
    2. The `docker build` command successfully creates a runnable container image of the agent.

- **Story 2.4: Create a CI/CD Pipeline for Deployment**

  - **As a** developer, **I want** to create a basic CI/CD pipeline (using GitHub Actions) that attempts to deploy the patched manifests to our test AKS cluster, **so that** the agent's full workflow can be triggered automatically.
  - **Acceptance Criteria:**
    1. A GitHub Actions workflow file is configured in the repository.
    2. When triggered, the workflow builds the container and runs the deployment command against the test AKS cluster.

- **Story 2.5: Implement Final Status Notification**
  - **As a** developer, **I want** the agent's pipeline to send a final success or failure notification to Slack, **so that** users are informed of the outcome.
  - **Acceptance Criteria:**
    1. After the deployment step, a message is successfully posted to a configured Slack channel with the deployment status.

---

This section contains the official handoff prompts for the next agents in the workflow.

**Handoff to UX Expert**

- Since our MVP does not include a graphical user interface, no handoff to the UX Expert is needed at this time.

**Handoff to Architect**

> This Product Requirements Document (PRD), along with the `aks-copilot.pdf`, provides the complete functional requirements and vision for the project. Please create the **Architecture Document** based on these inputs.
>
> Pay close attention to the **Technical Assumptions** we've defined, including the serverless/event-driven approach and the requirement for a configurable system. The architecture should provide a detailed technical blueprint for the two epics defined for the MVP.

---
