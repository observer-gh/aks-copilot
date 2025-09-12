# src/llm/providers.py
import json
import http.client


def ollama_generate(model: str, prompt: str) -> str:
    """
    Calls local Ollama /api/generate with stream=false.
    Returns the raw 'response' text.
    """
    conn = http.client.HTTPConnection("localhost", 11434, timeout=60)
    body = json.dumps({"model": model, "prompt": prompt, "stream": False})
    conn.request("POST", "/api/generate", body,
                 {"Content-Type": "application/json"})
    r = conn.getresponse()
    if r.status != 200:
        raise RuntimeError(f"Ollama generate HTTP {r.status}")
    data = json.loads(r.read())
    # response may contain trailing whitespace/newlines
    return data.get("response", "").strip()
