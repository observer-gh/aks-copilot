# src/patch/dryrun.py
from typing import Any, List, Tuple
import copy
import yaml


def _json_pointer_exists(doc: Any, pointer: str) -> Tuple[bool, Any, Any, str]:
    """
    Returns (exists, parent, key_or_index, reason) for a single YAML doc.
    If pointer exists, parent is the container holding the target, and key_or_index is the final step.
    """
    if not pointer.startswith("/"):
        return False, None, None, "pointer must start with /"
    cur = doc
    parent = None
    key = None
    parts = [p for p in pointer.split("/")[1:] if p != ""]
    for i, p in enumerate(parts):
        parent = cur
        key = p
        if isinstance(cur, list):
            try:
                idx = int(p)
            except ValueError:
                return False, None, None, f"non-int index {p}"
            if idx < 0 or idx >= len(cur):
                return False, None, None, f"list index out of range: {p}"
            cur = cur[idx]
        elif isinstance(cur, dict):
            if p not in cur:
                if i == len(parts) - 1:
                    # last step can be created for 'add'
                    return False, parent, key, "final step missing"
                return False, None, None, f"missing key: {p}"
            cur = cur[p]
        else:
            return False, None, None, "mid-node is neither list nor dict"
    return True, parent, key, ""


def _apply_single_op(doc: Any, op: dict) -> Tuple[bool, Any, str]:
    """
    Apply a single JSON Patch op to a YAML doc (supports add/replace).
    Returns (ok, new_doc, reason).
    """
    new_doc = copy.deepcopy(doc)
    o, path, val = op.get("op"), op.get("path"), op.get("value")
    if o not in ("add", "replace"):
        return False, doc, f"unsupported op: {o}"
    exists, parent, key, reason = _json_pointer_exists(new_doc, path)
    # replace requires existing
    if o == "replace":
        if not exists:
            return False, doc, f"replace path not found: {reason or path}"
        if isinstance(parent, list):
            try:
                idx = int(key)
            except ValueError:
                return False, doc, f"invalid list index: {key}"
            parent[idx] = val
        elif isinstance(parent, dict):
            parent[key] = val
        else:
            return False, doc, "replace parent is not list/dict"
    # add: allow creating the final step if missing
    elif o == "add":
        if exists:
            # treat add-on-existing as overwrite=not allowed for our guard
            return False, doc, "add would overwrite existing value"
        # when final step missing, parent/key returned if last hop missing
        if parent is None:
            return False, doc, "cannot add at root via pointer"
        if isinstance(parent, list):
            try:
                idx = int(key)
            except ValueError:
                return False, doc, f"invalid list index for add: {key}"
            if idx == len(parent):
                parent.append(val)
            elif 0 <= idx < len(parent):
                # adding into existing index is ambiguous -> forbid
                return False, doc, "add at existing list index forbidden"
            else:
                return False, doc, "add index out of range"
        elif isinstance(parent, dict):
            if key in parent:
                return False, doc, "add key already exists"
            parent[key] = val
        else:
            return False, doc, "add parent is not list/dict"
    return True, new_doc, ""


def dry_run_apply(yaml_text: str, ops: List[dict]) -> Tuple[bool, str]:
    """
    Try to apply ops to one of the YAML docs in the stream. All ops must succeed
    (each applies to whichever doc contains its path). Returns (ok, reason).
    """
    try:
        docs = list(yaml.safe_load_all(yaml_text))
    except Exception as e:
        return False, f"yaml parse error: {e}"

    # For simplicity, attempt each op against all docs until one succeeds.
    for op in ops:
        applied = False
        last_reason = "no doc matched"
        for i in range(len(docs)):
            ok, new_doc, reason = _apply_single_op(docs[i], op)
            if ok:
                docs[i] = new_doc
                applied = True
                break
            last_reason = reason
        if not applied:
            return False, f"dry-run failed: {last_reason}"
    return True, ""
