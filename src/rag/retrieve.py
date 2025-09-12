import json
import pathlib
from typing import List, Tuple, Dict
import faiss
import numpy as np
from src.rag.embedder import embed_texts


class Retriever:
    def __init__(self, vec_path="rag_index.faiss", meta_path="rag_meta.json"):
        self.index = faiss.read_index(vec_path)
        self.meta = json.loads(pathlib.Path(
            meta_path).read_text(encoding="utf-8"))["meta"]

    def search(self, query: str, k=2) -> List[Dict]:
        qv = np.array(embed_texts([query]), dtype="float32")
        faiss.normalize_L2(qv)
        D, I = self.index.search(qv, k)
        out = []
        for idx, score in zip(I[0], D[0]):
            if idx == -1:
                continue
            m = dict(self.meta[idx])
            m["score"] = float(score)
            out.append(m)
        return out


def load_chunk(meta: Dict) -> Tuple[str, str]:
    path = meta["source"]
    chunk_no = meta["chunk"]
    text = pathlib.Path(path).read_text(encoding="utf-8")
    # naive re-chunk identical to indexer
    parts = text.splitlines()
    buf, chunks, count = [], [], 0
    for line in parts:
        if count + len(line) > 400 and buf:
            chunks.append("\n".join(buf).strip())
            buf = []
            count = 0
        buf.append(line)
        count += len(line)+1
    if buf:
        chunks.append("\n".join(buf).strip())
    ch = chunks[chunk_no] if chunk_no < len(chunks) else ""
    # source link: for now, use file path; can map to official URL later
    return ch, path
