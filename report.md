# Migration Copilot Report

**Violations Found**
**File:** examples/enemy/deploy.yml
- SC002 container/app /spec/template/spec/containers/0/resources
  Found: missing requests/limits
  Expected: define cpu/memory requests and limits
  Severity: error
  Patch: auto (JSON Patch prepared)
  Why: # Container Requests & Limits (Scheduling & QoS)
  Source: kb/requests_limits.md

**File:** examples/enemy/pvc.yml
- SC001 PersistentVolumeClaim/web-data /spec/storageClassName
  Found: local-path
  Expected: managed-csi
  Severity: error
  Patch: auto (JSON Patch prepared)
  Why: # AKS Storage Classes (Managed CSI)
  Source: kb/aks_storage.md


Total violations: 2