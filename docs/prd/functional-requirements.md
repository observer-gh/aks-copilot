# Functional Requirements

**FR1:** The agent must analyze local Kubernetes manifest files to find configurations that are incompatible with AKS.

**FR2:** It must generate a `report.md` that details all violations, provides a clear explanation for why each change is necessary, and shows the patches it created.

**FR3:** It must generate a `resources.md` file listing the required Azure resources.

**FR4:** It must produce a set of patched, AKS-ready manifest files.

**FR5:** The user must be able to review and manually edit the generated manifests before the deployment attempt.

**FR6:** As part of the MVP, it must attempt a one-time deployment of the patched manifests to a target AKS namespace.

---
