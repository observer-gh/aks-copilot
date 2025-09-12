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

**File:** examples/enemy/ing.yml
- SC003 web /spec
  Found: no ingressClass/AGIC
  Expected: define ingressClassName or AGIC annotations
  Severity: error
  Patch: manual (no auto-fix)
  LLM suggestion (preview only):
    ---
    spec:
      ingress:
        className: azure/application-gateway
      annotations:
        kubernetes.io/ingress.class: azure/application-gateway
    ---
      ingress:
        annotation: 
          kubernetes.io/ingress.class: azure/application-gateway
  Why: # Ingress on AKS (AGIC Basics)
  Source: kb/ingress_agic.md

**File:** examples/enemy/ingress_bad.yml
- SC003 bad-ing /spec
  Found: no ingressClass/AGIC
  Expected: define ingressClassName or AGIC annotations
  Severity: error
  Patch: manual (no auto-fix)
  LLM suggestion (preview only):
    spec:
      ingress:
        annotations:
          kubernetes.io/ingress.class: "azure/application-gateway"
  Why: # Ingress on AKS (AGIC Basics)
  Source: kb/ingress_agic.md

**File:** examples/enemy/pvc.yml
- SC001 PersistentVolumeClaim/web-data /spec/storageClassName
  Found: local-path
  Expected: managed-csi
  Severity: error
  Patch: auto (JSON Patch prepared)
  Note: chose 'managed-csi' (live classes: azurefile, azurefile-csi, azurefile-csi-premium, azurefile-premium, default, managed, managed-csi, managed-csi-premium, managed-premium)
  Why: # AKS Storage Classes (Managed CSI)
  Source: kb/aks_storage.md


Total violations: 4