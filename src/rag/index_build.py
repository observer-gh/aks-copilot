import json
import pathlib
from typing import List, Dict
import faiss
import numpy as np
from src.rag.embedder import embed_texts


def _chunk(text: str, max_chars=400) -> List[str]:
    parts, cur = [], []
    count = 0
    for line in text.splitlines():
        if count + len(line) > max_chars and cur:
            parts.append("\n".join(cur).strip())
            cur, count = [], 0
        cur.append(line)
        count += len(line) + 1
    if cur:
        parts.append("\n".join(cur).strip())
    return [p for p in parts if p]


def build_index(kb_dir="kb", out_vec="rag_index.faiss", out_meta="rag_meta.json"):
    kb = pathlib.Path(kb_dir)
    chunks: List[str] = []
    meta: List[Dict] = []
    for md in sorted(kb.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for i, ch in enumerate(_chunk(text)):
            chunks.append(ch)
            meta.append({"source": str(md), "chunk": i})
    if not chunks:
        raise SystemExit("no KB chunks")

    vecs = embed_texts(chunks)
    dim = len(vecs[0])
    index = faiss.IndexFlatIP(dim)
    # normalize for cosine similarity
    X = np.array(vecs, dtype="float32")
    faiss.normalize_L2(X)
    index.add(X)

    faiss.write_index(index, out_vec)
    pathlib.Path(out_meta).write_text(json.dumps(
        {"meta": meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"built index: {len(chunks)} chunks, dim={dim}")


if __name__ == "__main__":
    build_index()
