import json
import http.client
from typing import List
from src.config import get_config


def _ollama_embed(texts: List[str], model: str) -> List[List[float]]:
    conn = http.client.HTTPConnection("localhost", 11434, timeout=30)
    body = json.dumps({"model": model, "input": texts})
    conn.request("POST", "/api/embed", body,
                 {"Content-Type": "application/json"})
    r = conn.getresponse()
    if r.status != 200:
        raise RuntimeError(f"Ollama embeddings HTTP {r.status}")
    data = json.loads(r.read())
    # supports both single and batched responses
    vecs = data.get("embeddings") or [data.get("embedding")]
    if not vecs or not vecs[0]:
        raise RuntimeError("empty embeddings from ollama")
    return vecs


def _stub_embed(texts: List[str]) -> List[List[float]]:
    # deterministic tiny hash → 16-dim toy vector (placeholder)
    out = []
    for t in texts:
        v = [((sum(bytearray(t.encode())) + i*17) % 97)/97.0 for i in range(16)]
        out.append(v)
    return out


def embed_texts(texts: List[str]) -> List[List[float]]:
    cfg = get_config()
    provider = cfg.get("embedder", "stub")
    if provider == "ollama":
        model = cfg.get("embedder_model", "nomic-embed-text")
        return _ollama_embed(texts, model)
    return _stub_embed(texts)
