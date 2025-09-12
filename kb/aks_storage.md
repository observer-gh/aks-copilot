# AKS Storage Classes (Managed CSI)

AKS uses managed disks via CSI. For production, prefer managed CSI classes (e.g., managed-csi / managed-premium).

Why it matters:

- k3s `local-path` is single-node; not suitable for multi-node AKS.
- Managed CSI provides durability, zoning, and autoscaling compatibility.

Key points:

- Use StorageClass with CSI drivers provided by AKS.
- Match PVC `storageClassName` to an AKS-managed class.

Source:
https://learn.microsoft.com/azure/aks/concepts-storage
