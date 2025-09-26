from __future__ import annotations
from typing import List, Dict, Sequence, Any
import json
from pathlib import Path
from datetime import datetime
from src.patch.validator import validate_patch_ops
from src.llm.logger import log_llm

SCHEMA_VERSION = 1


def _wrap_suggestions(suggestions: List[Dict], rule: str | None) -> Dict:
    valid_count = sum(1 for s in suggestions if s.get("valid"))
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "rule": rule,
        "meta": {"total": len(suggestions), "valid": valid_count},
        "suggestions": suggestions,
    }


def write_suggestions(suggestions: List[Dict], path: str = "suggestions.json", rule: str | None = None):
    """Write suggestions file using wrapper schema. Backward compatible reader handles legacy arrays."""
    wrapped = _wrap_suggestions(suggestions, rule)
    Path(path).write_text(json.dumps(wrapped, indent=2), encoding="utf-8")


def load_suggestions(path: str = "suggestions.json") -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, list):  # legacy format
        return data
    if isinstance(data, dict) and isinstance(data.get("suggestions"), list):
        return data["suggestions"]
    return []


def filter_approved(all_suggestions: List[Dict], approved: Sequence[int] | None) -> List[Dict]:
    if not approved:
        # default: take all valid suggestions
        return [s for s in all_suggestions if s.get("valid")]
    approved_set = set(int(i) for i in approved)
    out = []
    for s in all_suggestions:
        if s.get("index") in approved_set and s.get("valid"):
            out.append(s)
    return out


def merge_suggestions_into_patch(existing_patch: List[Dict], suggestions: List[Dict], collect_details: bool = False) -> tuple[List[Dict], Dict]:
    """
    Merge suggestion envelopes (each with file/resource/ops) into existing patch envelopes.
    Policy:
      - If an envelope (file+resource.kind+resource.name) exists, append non-duplicate ops.
      - Duplicate path (same op+path+value) skipped silently (counted in stats).
      - Same path different value -> keep last (replace previous by appending; consumer applies sequentially) and count as conflict.
    Returns (new_patch, stats) where stats = {merged, skipped_duplicates, conflicts}.
    """
    by_key = {}
    for env in existing_patch:
        key = (env.get("file"), (env.get("resource") or {}).get(
            "kind"), (env.get("resource") or {}).get("name"))
        by_key.setdefault(key, env)

    # stats dict: dynamic value types (ints and optional list for details)
    stats: Dict[str, Any] = {"merged": 0,
                             "skipped_duplicates": 0, "conflicts": 0}
    if collect_details:
        # list of {file, path, previous, new, previous_op, new_op}
        stats["conflict_details"] = []

    for sug in suggestions:
        file = sug.get("file")
        res = sug.get("resource") or {}
        key = (file, res.get("kind"), res.get("name"))
        ops = sug.get("ops", [])
        ok, reason = validate_patch_ops(ops)
        if not ok:
            log_llm({"event": "merge", "stage": "validate_ops",
                    "success": False, "reason": reason})
            continue
        env = by_key.get(key)
        if not env:
            # new envelope
            env = {"file": file, "resource": res, "ops": []}
            existing_patch.append(env)
            by_key[key] = env
        for op in ops:
            dup = next((o for o in env["ops"] if o.get("op") == op.get("op") and o.get(
                "path") == op.get("path") and o.get("value") == op.get("value")), None)
            if dup:
                stats["skipped_duplicates"] += 1
                log_llm({"event": "merge.duplicate",
                        "file": file, "path": op.get("path")})
                continue
            conflict = next((o for o in env["ops"] if o.get("path") == op.get("path") and (
                o.get("value") != op.get("value") or o.get("op") != op.get("op"))), None)
            if conflict:
                stats["conflicts"] += 1
                detail = {"file": file, "path": op.get("path"), "previous": conflict.get(
                    "value"), "new": op.get("value"), "previous_op": conflict.get("op"), "new_op": op.get("op")}
                log_llm({"event": "merge.conflict",
                        "file": file, "path": op.get("path"), "previous": conflict.get("value"), "new": op.get("value")})
                if collect_details:
                    stats["conflict_details"].append(detail)
            env["ops"].append(op)
            stats["merged"] += 1
            log_llm({"event": "merge.add", "file": file, "path": op.get("path")})
    log_llm({"event": "merge.summary", **stats})
    return existing_patch, stats
