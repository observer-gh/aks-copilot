import json
from typing import Dict, Any
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
