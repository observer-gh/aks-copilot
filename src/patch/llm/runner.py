# src/patch/llm/runner.py
import json
from typing import List, Tuple
import yaml
from src.patch.llm.validator import validate_sc002_ops
from src.config import get_config


def DEFAULT_OP(path: str):
    c = get_config()["sc002"]
    return [{
        "op": "add",
        "path": f"{path}/resources",
        "value": {
            "requests": {"cpu": c["cpu_requests"], "memory": c["mem_requests"]},
            "limits":   {"cpu": c["cpu_limits"],  "memory": c["mem_limits"]}
        }
    }]


def _extract_container_path(kind: str, index: int) -> str:
    if kind in ("Deployment", "StatefulSet"):
        return f"/spec/template/spec/containers/{index}"
    return f"/spec/containers/{index}"  # Pod


def suggest_sc002_ops(kind: str, container_index: int, yaml_text: str) -> Tuple[List[dict], str]:
    """
    Stub: pretend an LLM suggested the default op for SC002, then validate.
    Returns (ops, reason_if_empty)
    """
    container_path = _extract_container_path(kind, container_index)
    ops = DEFAULT_OP(container_path)  # stand-in for LLM output
    ok, reason = validate_sc002_ops(ops, container_path, yaml_text)
    if ok:
        return ops, ""
    return [], reason
