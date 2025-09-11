# src/inspect/storageclass.py
from typing import List, Dict
import yaml

SC_BAD = "local-path"
SC_GOOD = "managed-csi"


def inspect_storageclass(manifest_yaml: str) -> List[Dict]:
    """
    Input: a single Kubernetes YAML string (one or more docs, '---' separated)
    Output: list of violation dicts (empty if none)
    Emits SC001 when a PVC has spec.storageClassName == "local-path"
    """
    violations: List[Dict] = []
    try:
        docs = list(yaml.safe_load_all(manifest_yaml))
    except Exception:
        # If YAML is invalid, return empty for MVP (or raise in future)
        return violations

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        if doc.get("kind") != "PersistentVolumeClaim":
            continue

        meta = doc.get("metadata", {}) or {}
        spec = doc.get("spec", {}) or {}
        name = meta.get("name", "<unknown>")
        scn = spec.get("storageClassName")

        if scn == SC_BAD:
            violations.append({
                "id": "SC001",
                "resource": f"PersistentVolumeClaim/{name}",
                "path": "/spec/storageClassName",
                "found": SC_BAD,
                "expected": SC_GOOD,
                "severity": "error",
                "rule": "storageClass.k3s_to_aks",
            })

    return violations
