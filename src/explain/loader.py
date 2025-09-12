# src/explain/loader.py
import json
import pathlib
from typing import Dict
from src.rag.retrieve import Retriever, load_chunk

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (…/aksmigrate)
RULES_DIR = ROOT / "rules"
INDEX_FILE = RULES_DIR / "index.json"

_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        try:
            _retriever = Retriever()
        except Exception:
            _retriever = None
    return _retriever


QUERIES = {
    "SC001": "AKS storage class managed CSI vs local-path why",
    "SC002": "kubernetes why set container requests limits QoS HPA",
}


def load_explanation(rule_id: str) -> Dict[str, str]:
    """
    Returns { 'why': str, 'source': str } for the given rule_id.
    Tries RAG retrieval first, falls back to static rules.
    """
    r = _get_retriever()
    if r and rule_id in QUERIES:
        hits = r.search(QUERIES[rule_id], k=1)
        if hits:
            chunk, src = load_chunk(hits[0])
            # first 2 sentences or ~200 chars
            why = (chunk.split("\n\n")[0] or chunk)[:200]
            return {"why": why, "source": src}

    # fallback to static rules
    try:
        idx = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        md_name = idx.get(rule_id)
        if not md_name:
            return {"why": "", "source": ""}

        md_path = RULES_DIR / md_name
        if not md_path.exists():
            return {"why": "", "source": ""}

        why, src = "", ""
        for line in md_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.lower().startswith("why:"):
                why = line.split(":", 1)[1].strip()
            elif line.lower().startswith("source:"):
                src = line.split(":", 1)[1].strip()
        return {"why": why, "source": src}
    except Exception:
        return {"why": "", "source": ""}
