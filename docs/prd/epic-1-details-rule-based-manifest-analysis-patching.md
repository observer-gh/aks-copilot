# Epic 1 Details: Rule-Based Manifest Analysis & Patching

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
