# src/patch/validator.py
from typing import Any, List, Dict
import yaml


def _get_by_pointer(doc: Any, pointer: str) -> tuple[bool, Any]:
    if not pointer.startswith("/"):
        return False, None
    cur = doc
    parts = [p for p in pointer.split("/")[1:] if p != ""]
    for p in parts:
        # list index?
        if isinstance(cur, list):
            try:
                idx = int(p)
            except ValueError:
                return False, None
            if idx < 0 or idx >= len(cur):
                return False, None
            cur = cur[idx]
        elif isinstance(cur, dict):
            if p not in cur:
                return False, None
            cur = cur[p]
        else:
            return False, None
    return True, cur


def path_exists_in_yaml(yaml_text: str, pointer: str) -> bool:
    """
    Returns True if any doc in the YAML stream contains JSON-Pointer `pointer`.
    """
    try:
        for doc in yaml.safe_load_all(yaml_text):
            ok, _ = _get_by_pointer(doc, pointer)
            if ok:
                return True
    except Exception:
        return False
    return False


# --- Story 2.2 additions: op validation for AI suggestions / merge safety ---
_FORBIDDEN_PREFIXES = (
    "/metadata/uid",
    "/metadata/creationTimestamp",
    "/metadata/managedFields",
    "/status",
)

PER_SUGGESTION_MAX_OPS = 10  # Story 2.2 Phase 2 cap


def is_forbidden_path(path: str) -> bool:
    if not isinstance(path, str):
        return True
    return any(path.startswith(p) for p in _FORBIDDEN_PREFIXES)


def validate_patch_ops(ops: List[Dict]) -> tuple[bool, str]:
    if not isinstance(ops, list):
        return False, "ops not list"
    if len(ops) > 50:
        return False, "too many ops (global)"
    if len(ops) > PER_SUGGESTION_MAX_OPS:
        return False, "too many ops in suggestion"
    for op in ops:
        if not isinstance(op, dict):
            return False, "op not dict"
        if op.get("op") not in ("add", "replace"):
            return False, f"unsupported op {op.get('op')}"
        p = op.get("path")
        if not isinstance(p, str) or not p.startswith("/"):
            return False, "invalid path"
        if is_forbidden_path(p):
            return False, f"forbidden path {p}"
        # size guard
        if "value" in op:
            try:
                import json
                if len(json.dumps(op["value"])) > 8192:
                    return False, "value too large"
            except Exception:
                return False, "value not serializable"
    return True, ""
