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
            op = {"op": "replace", "path": v["path"], "value": sc, "file": v["file"]}
            if use_live:
                sc_ops, chosen_sc, live_set = sc001_patch_ops(
                    "", use_live=True)
                # We are only expecting one op for SC001
                op["value"] = sc_ops[0]["value"]

            ops.append(op)
        # SC002 → manual (no auto-fix in v0)
    return ops


def build_patch_ops(violations: List[Dict], use_live: bool = False) -> List[Dict]:
    """
    Adapter that returns per-file envelope list of patch ops.
    Each envelope: {"file": str, "resource": {"kind":..., "name":...} (optional), "ops": [ ... ]}
    Validates minimal violation shape (rule_id or id, file, path, desired)
    """
    if not isinstance(violations, list):
        raise ValueError("violations must be a list of dicts")

    envelopes: List[Dict] = []
    # normalize: allow 'rule_id' or 'id'
    for v in violations:
        if not isinstance(v, dict):
            raise ValueError("each violation must be a dict")
        rule = v.get("rule_id") or v.get("id")
        file = v.get("file")
        path = v.get("path")
        desired = v.get("desired")
        if not rule or not file or not path:
            raise ValueError(
                "violation missing required keys: rule_id/id, file, path")

        # currently only SC001 -> replace storageClassName
        if rule in ("SC001", "sc001"):
            if desired is None:
                # fallback to config default
                desired = get_config().get("defaultSC", "managed-csi")
            op = {"op": "replace", "path": path, "value": desired}
            env = {"file": file, "resource": {"kind": v.get(
                "kind"), "name": v.get("name")}, "ops": [op]}
            envelopes.append(env)
        elif rule in ("SC002", "sc002"):
            # SC002: add or replace resources at the container resources path
            desired = v.get("desired")
            if desired is None:
                # nothing to do
                continue
            # op: if current missing -> add, else replace
            # inspector provides current -> decide
            cur = v.get("current")
            if not cur:
                op = {"op": "add", "path": v["path"], "value": desired}
            else:
                # replace entire resources block
                op = {"op": "replace", "path": v["path"], "value": desired}
            env = {"file": v.get("file"), "resource": {"kind": v.get(
                "kind"), "name": v.get("name")}, "ops": [op]}
            envelopes.append(env)
        else:
            # unknown rule -> skip or raise? choose to skip for now
            continue
    return envelopes


def write_patch_json(patches: List[Dict], out_path: str):
    import json
    from pathlib import Path

    p = Path(out_path)
    p.write_text(json.dumps(patches, indent=2), encoding="utf-8")
