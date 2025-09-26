import json
import os
from typing import List
import numpy as np
import requests
from src.config import get_config


def _ollama_embed(texts: List[str], model: str) -> List[List[float]]:
    """
    Embeds a list of texts using a running Ollama instance.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    url = f"{base_url}/api/embeddings"

    results = []
    # Ollama's /api/embeddings endpoint processes one prompt at a time.
    for text in texts:
        payload = {"model": model, "prompt": text}
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if "embedding" in data:
                results.append(data["embedding"])
        except requests.exceptions.RequestException as e:
            print(
                f"[ERROR] Ollama embed request failed for text '{text[:50]}...': {e}")
            # On failure, we can't generate a meaningful embedding.
            # Returning an empty list will cause the search to find no results.
            return []
    return results


def _stub_embed(texts: List[str]) -> List[List[float]]:
    # consistent, but meaningless, embeddings
    return [[hash(txt) / 1e10, (hash(txt) >> 32) / 1e10] for txt in texts]


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Embed a list of texts using the configured provider.
    Returns a numpy array of embeddings.
    """
    cfg = get_config()
    provider = cfg.get("embedder", "stub")
    if provider == "ollama":
        model = cfg.get("embedder_model", "nomic-embed-text")
        embeddings = _ollama_embed(texts, model)
        if embeddings:
            return np.array(embeddings, dtype="float32")

    # Fallback to stub if provider is not ollama or if embedding fails
    return np.array(_stub_embed(texts), dtype="float32")
