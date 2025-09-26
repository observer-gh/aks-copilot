import json
from typing import Dict, Any, List
import yaml
from src.config import get_config
from src.llm.client import build_client, hash_prompt, LLMTimeout, LLMError
from src.llm.prompts import EXPLAIN_VIOLATION_TEMPLATE, SUGGEST_IMPROVEMENT_TEMPLATE
from src.llm.logger import log_llm


def _llm_cfg():
    root = get_config()
    raw = root.get("llm")
    # Legacy style: "llm": "ollama" and separate llm_model
    if isinstance(raw, str):
        return {
            "enabled": True,
            "provider": raw,
            "model": root.get("llm_model", "mistral:latest"),
            "timeout_seconds": root.get("llm_timeout_seconds", 8),
            "max_output_chars": root.get("llm_max_output_chars", 2000),
        }
    if isinstance(raw, dict):
        # ensure enabled defaults to value or true if provider present
        if "enabled" not in raw:
            raw = {**raw, "enabled": True}
        return raw
    return {"enabled": False}


def augment_explanation(violation: Dict[str, Any]) -> str:
    cfg = _llm_cfg()
    client = build_client(cfg)
    if not client:
        # deterministic fallback (empty or simple static sentence)
        return ""
    prompt = EXPLAIN_VIOLATION_TEMPLATE.format(**{
        "id": violation.get("id"),
        "resource": violation.get("resource"),
        "found": violation.get("found"),
        "expected": violation.get("expected"),
    })
    h = hash_prompt(prompt)
    truncated = False
    try:
        out = client.generate(prompt)
        if len(out) > cfg.get("max_output_chars", 2000):
            out = out[: cfg.get("max_output_chars", 2000)]
            truncated = True
        log_llm({"event": "explain", "rule": violation.get("id"),
                "hash": h, "success": True, "truncated": truncated})
        return out
    except LLMTimeout as e:
        log_llm({"event": "explain", "rule": violation.get("id"),
                "hash": h, "success": False, "error": "timeout"})
        return ""
    except Exception as e:  # noqa
        log_llm({"event": "explain", "rule": violation.get("id"),
                "hash": h, "success": False, "error": str(e)[:120]})
        return ""


def generate_suggestion(violation: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _llm_cfg()
    client = build_client(cfg)
    if not client:
        return {"type": "patch_suggestion", "ops": []}
    raw_violation = json.dumps({k: v for k, v in violation.items() if k in (
        "id", "path", "desired", "current", "resource")})
    prompt = SUGGEST_IMPROVEMENT_TEMPLATE.format(violation_json=raw_violation)
    h = hash_prompt(prompt)
    try:
        out = client.generate(prompt)
        data = json.loads(out)
        if not _validate_suggestion(data):
            raise LLMError("invalid suggestion schema")
        log_llm({"event": "suggest", "rule": violation.get("id"),
                "hash": h, "success": True, "ops": len(data.get("ops", []))})
        return data
    except Exception as e:  # timeout, parse, schema
        log_llm({"event": "suggest", "rule": violation.get("id"),
                "hash": h, "success": False, "error": str(e)[:120]})
        return {"type": "patch_suggestion", "ops": []}


# --- SC003 heuristic (Phase 3) ---
def heuristic_sc003_ops(violation: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Produce deterministic fallback ops for an Ingress (SC003) when LLM disabled or empty.
    Heuristics:
      - If /spec/ingressClassName missing -> add with value "web" (placeholder class).
      - If /spec/tls missing AND spec.rules[0].host present -> add minimal tls list with secretName <name>-tls.
    Returns list of JSON Patch ops (add only). Safe to call even if file missing; returns empty on failure.
    """
    if (violation.get("rule_id") or violation.get("id")) != "SC003":
        return []
    file_path = violation.get("file")
    name = violation.get("name") or violation.get("resource") or "ingress"
    if not file_path:
        return []
    try:
        text = open(file_path, "r", encoding="utf-8").read()
    except Exception:
        return []
    try:
        docs = list(yaml.safe_load_all(text))
    except Exception:
        return []
    target = None
    for d in docs:
        if not isinstance(d, dict):
            continue
        if d.get("kind") == "Ingress":
            meta = d.get("metadata") or {}
            if not name or meta.get("name") == name:
                target = d
                break
    if not target:
        return []
    spec = target.get("spec") or {}
    ops: List[Dict[str, Any]] = []
    if "ingressClassName" not in spec:
        ops.append(
            {"op": "add", "path": "/spec/ingressClassName", "value": "web"})
    tls_missing = "tls" not in spec
    # attempt TLS heuristic
    host = None
    rules = spec.get("rules") if isinstance(spec.get("rules"), list) else []
    if rules and isinstance(rules[0], dict):
        host = rules[0].get("host")
    if tls_missing and host:
        secret = f"{name}-tls" if name else "ingress-tls"
        tls_value = [{"hosts": [host], "secretName": secret}]
        ops.append({"op": "add", "path": "/spec/tls", "value": tls_value})
    if ops:
        log_llm({"event": "suggest.heuristic", "rule": "SC003", "ops": len(ops)})
    return ops


def generate_resource_suggestions(violations: List[Dict[str, Any]], rule_filter: str | None = None) -> List[Dict[str, Any]]:
    """Batch helper: produce raw suggestion dicts (with ops) for violations.
    Applies LLM suggestion first, then heuristic fallback (currently SC003) if no ops.
    rule_filter restricts processing to a single rule id when provided.
    Returned list items DO NOT include index/validation flags (caller adds those).
    """
    out: List[Dict[str, Any]] = []
    for v in violations:
        rid = v.get("rule_id") or v.get("id")
        if rule_filter and rid != rule_filter:
            continue
        sugg = generate_suggestion(v)
        ops = sugg.get("ops", [])
        if not ops and rid == "SC003":  # heuristic fallback
            ops = heuristic_sc003_ops(v)
        out.append({
            "rule_id": rid,
            "file": v.get("file"),
            "kind": v.get("kind"),
            "name": v.get("name"),
            "ops": ops,
            "explanation": sugg.get("explanation", ""),
        })
    return out


def _validate_suggestion(obj: Dict[str, Any]) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("type") != "patch_suggestion":
        return False
    ops = obj.get("ops")
    if not isinstance(ops, list):
        return False
    for op in ops:
        if not isinstance(op, dict):
            return False
        if op.get("op") not in ("add", "replace"):
            return False
        if not isinstance(op.get("path"), str):
            return False
    return True
