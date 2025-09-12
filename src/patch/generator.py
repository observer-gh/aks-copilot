# src/patch/generator.py
from typing import List, Dict
from src.config import get_config


def build_patches(violations: List[Dict]) -> List[Dict]:
    """
    Return JSON Patch ops for auto-fixable rules.
    v0: SC001 only (storageClassName replace).
    """
    ops: List[Dict] = []
    cfg = get_config()
    sc = cfg.get("defaultSC", "managed-csi")
    for v in violations:
        if v.get("id") == "SC001":
            ops.append({"op": "replace", "path": v["path"], "value": sc})
        # SC002 → manual (no auto-fix in v0)
    return ops
