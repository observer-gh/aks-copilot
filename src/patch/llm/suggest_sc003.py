import json
from src.llm.providers import ollama_generate
from src.config import get_config
from src.llm.logger import log_llm


def suggest_sc003_preview(file_path: str, kind: str = "Ingress", path: str = "/spec"):
    """
    Return a string suggestion (YAML snippet) for ingressClassName or AGIC annotations.
    Not applied; only shown in report. Safe-guarded by config.llm.
    """
    cfg = get_config()
    if cfg.get("llm") != "ollama":
        return ""  # no suggestion if LLM disabled

    model = cfg.get("llm_model", "llama3.2:latest")
    prompt = f"""You are a Kubernetes migration assistant.
Given an {kind} manifest missing ingress class or AGIC annotations at {path},
suggest ONE safe example YAML snippet (only the fields to add) for AKS:
- Option A: set ingressClassName: "azure/application-gateway"
- Option B: add AGIC annotations block for application gateway
IMPORTANT:
- Output YAML only, no prose, no code fences.
- Keep it minimal and generic; do not include unrelated fields."""
    raw = ollama_generate(model, prompt).strip()
    log_llm({"file": file_path, "rule": "SC003",
             "stage": "llm_suggest", "ok": True, "raw": raw[:400]})

    # Clean up the response: remove code fences and extract YAML
    if raw.startswith("```"):
        # Extract content between code fences
        lines = raw.split("\n")
        yaml_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                yaml_lines.append(line)
        raw = "\n".join(yaml_lines).strip()

    # lightweight sanity: must look like YAML key: value
    if ":" not in raw:
        return ""
    return raw
