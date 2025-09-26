# src/llm/providers.py
import json
import os
import requests


def ollama_generate(model: str, prompt: str) -> str:
    """
    Calls local Ollama /api/generate with stream=false.
    Returns the raw 'response' text.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    url = f"{base_url}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()  # Raise an exception for 4xx/5xx errors
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ollama request failed: {e}")
        return ""
