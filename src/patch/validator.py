# src/patch/validator.py
from typing import Any
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
