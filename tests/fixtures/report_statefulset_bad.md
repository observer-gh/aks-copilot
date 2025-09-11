# Migration Copilot Report

**File:** statefulset_bad.yml

**Violations Found**

- ID: SC001
  Resource: PersistentVolumeClaim/mydata
  Path: /spec/storageClassName
  Found: local-path
  Expected: managed-csi
  Severity: error
  Why: k3s local-path is single-node; AKS needs managed CSI.