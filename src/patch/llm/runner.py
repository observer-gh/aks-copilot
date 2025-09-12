# src/patch/llm/runner.py
import json
from typing import List, Tuple
import yaml
from src.patch.llm.validator import validate_sc002_ops
from src.config import get_config
from src.llm.providers import ollama_generate


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


def suggest_sc002_ops(kind: str, container_index: int, yaml_text: str, file_path: str) -> Tuple[List[dict], str]:
    """
    Generate SC002 JSON Patch ops using LLM or fallback to default.
    Returns (ops, reason_if_empty)
    """
    container_path = _extract_container_path(kind, container_index)
    cfg = get_config()
    if cfg.get("llm") == "ollama":
        model = cfg.get("llm_model", "llama3.2:latest")
        base_prompt = f"""You are a Kubernetes migration assistant.
TASK: Output ONLY a valid JSON Patch (RFC 6902) as a JSON array, nothing else.
Context: A {kind} manifest is missing requests/limits at {container_path}.
Constraints:
- Use 'add' op targeting "{container_path}/resources".
- Include: requests.cpu, requests.memory, limits.cpu, limits.memory.
- Values: cpu requests 100m, memory 128Mi, cpu limits 200m, memory 256Mi.
Output: JSON array only, no code fences, no explanations.
"""
        reason = "no valid patch"
        for attempt in range(2):  # max 2 tries
            prompt = base_prompt if attempt == 0 else base_prompt + \
                "\n\nREMINDER: Output must be JSON array only."
            raw = ollama_generate(model, prompt)
            try:
                from src.cli.main import _log_llm
                _log_llm({"file": file_path, "rule": "SC002",
                         "stage": f"llm_raw_try{attempt+1}", "ok": True, "raw": raw[:400]})
            except ImportError:
                pass  # fallback if _log_llm not accessible
            try:
                ops = json.loads(raw)
                ok, reason = validate_sc002_ops(ops, container_path, yaml_text)
                if ok:
                    return ops, ""
            except Exception as e:
                reason = f"invalid json: {e}"
        # after both attempts failed
        try:
            from src.cli.main import _log_llm
            _log_llm({
                "file": file_path,
                "rule": "SC002",
                "stage": "llm_fallback",
                "ok": False,
                "reason": reason
            })
        except ImportError:
            pass  # fallback if _log_llm not accessible
        # fallback to deterministic defaults so demo still shows "auto"
        ops = DEFAULT_OP(container_path)
        return ops, "llm failed, used defaults"
    else:
        ops = DEFAULT_OP(container_path)
        return ops, ""
