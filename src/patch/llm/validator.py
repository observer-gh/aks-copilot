# src/patch/llm/validator.py
from typing import List, Tuple, Any
import yaml


def _json_pointer_exists(yaml_text: str, pointer: str) -> bool:
    try:
        for doc in yaml.safe_load_all(yaml_text):
            cur: Any = doc
            parts = [p for p in pointer.split("/")[1:]]
            ok = True
            for p in parts:
                if isinstance(cur, list):
                    try:
                        i = int(p)
                    except ValueError:
                        ok = False
                        break
                    if i < 0 or i >= len(cur):
                        ok = False
                        break
                    cur = cur[i]
                elif isinstance(cur, dict):
                    if p not in cur:
                        ok = False
                        break
                    cur = cur[p]
                else:
                    ok = False
                    break
            if ok:
                return True
    except Exception:
        return False
    return False


def validate_sc002_ops(ops: List[dict], container_path: str, yaml_text: str) -> Tuple[bool, str]:
    # 1) basic shape
    if not isinstance(ops, list) or len(ops) == 0:
        return False, "ops must be non-empty list"
    op = ops[0]
    if not all(k in op for k in ("op", "path", "value")):
        return False, "missing op/path/value"
    # 2) op/path
    if op["op"] != "add":
        return False, "op must be add"
    expected_path = f"{container_path}/resources"
    if op["path"] != expected_path:
        return False, f"path must be {expected_path}"
    # 3) value fields
    val = op["value"]
    try:
        rc = val["requests"]["cpu"]
        rm = val["requests"]["memory"]
        lc = val["limits"]["cpu"]
        lm = val["limits"]["memory"]
    except Exception:
        return False, "value must include requests.cpu/memory and limits.cpu/memory"
    # 4) container path exists
    if not _json_pointer_exists(yaml_text, container_path):
        return False, "container path not found"
    # 5) will not overwrite existing
    # if resources already exists, it's risky in MVP
    if _json_pointer_exists(yaml_text, expected_path):
        return False, "resources already present; no overwrite allowed"
    # 6) bounds (very simple checks)
    if rc.endswith("m"):
        try:
            if int(rc[:-1]) > 1000:  # >1 core in millicores
                return False, "requests.cpu too large"
        except ValueError:
            return False, "invalid requests.cpu"
    if lc.endswith("m"):
        try:
            if int(lc[:-1]) > 2000:  # >2 cores in millicores
                return False, "limits.cpu too large"
        except ValueError:
            return False, "invalid limits.cpu"
    if not rm.endswith(("Mi", "Gi")) or not lm.endswith(("Mi", "Gi")):
        return False, "memory units must be Mi/Gi"
    return True, ""
