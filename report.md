# Migration Copilot Report

**Violations Found**
**File:** <input>
- SC001 PersistentVolumeClaim/mydata /spec/storageClassName
  Found: local-path
  Expected: managed-csi
  Severity: error
  Patch: auto (JSON Patch prepared)
  Why: k3s local-path is single-node only; AKS requires managed CSI.
  Source: https://learn.microsoft.com/en-us/azure/aks/concepts-storage


Total violations: 1