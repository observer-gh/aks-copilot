# src/patch/generator.py
from typing import List, Dict, Set, Optional, Tuple
from src.config import get_config


def choose_sc(default_sc: str, live_classes: Optional[Set[str]]) -> str:
    if live_classes:
        # prefer default if present, else pick any AKS-ish managed class
        if default_sc in live_classes:
            return default_sc
        for cand in ["managed-csi", "managed-premium", "default", "premium"]:
            if cand in live_classes:
                return cand
        # fallback: first live class
        return sorted(live_classes)[0]
    return default_sc


def sc001_patch_ops(yaml_text: str, use_live: bool = False) -> Tuple[List[Dict], str, Set[str]]:
    """
    Generate SC001 patch ops with optional live StorageClass detection.
    Returns (ops, chosen_sc, live_classes_set)
    """
    from src.live.kube import list_storage_classes
    from src.config import get_config

    cfg = get_config()
    default_sc = cfg.get("defaultSC", "managed-csi")
    live = list_storage_classes() if use_live else None
    chosen = choose_sc(default_sc, live)

    ops = [{
        "op": "replace",
        "path": "/spec/storageClassName",
        "value": chosen
    }]

    return ops, chosen, (live or set())


def build_patches(violations: List[Dict], use_live: bool = False) -> List[Dict]:
    """
    Return JSON Patch ops for auto-fixable rules.
    v0: SC001 only (storageClassName replace).
    """
    ops: List[Dict] = []
    cfg = get_config()
    sc = cfg.get("defaultSC", "managed-csi")
    for v in violations:
        if v.get("id") == "SC001":
            if use_live:
                sc_ops, chosen_sc, live_set = sc001_patch_ops(
                    "", use_live=True)
                ops.extend(sc_ops)
            else:
                ops.append({"op": "replace", "path": v["path"], "value": sc})
        # SC002 → manual (no auto-fix in v0)
    return ops
