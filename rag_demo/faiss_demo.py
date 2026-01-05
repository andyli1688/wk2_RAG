# Test

"""
1) 读取 `Speech and Language Processing.pdf`
2) 用 LangChain 分块（见 `document_process.py`）
3) 用 `embedding.py` 的 `local_embedding` 拿向量
4) 创建一个新的 FAISS index 并保存到本地
5) 做一次简单检索并打印结果
"""

from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Tuple

import faiss  
import numpy as np

from embedding import local_embedding
from document_process import chunk_pdf_texts

# ========= 你只需要看这里（默认不用改）=========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_FILE_PATH = os.path.join(BASE_DIR, "Speech and Language Processing.pdf")
OUT_DIR = os.path.join(BASE_DIR, "faiss_out")
INDEX_FILE_PATH = os.path.join(OUT_DIR, "slp.index.faiss")
META_FILE_PATH = os.path.join(OUT_DIR, "slp.meta.json")

# ========= Config =========
EMBEDDING_DIM = 1024
DEFAULT_TOP_K = 10
BATCH_SIZE = 25  

def _batched(items: List[str], batch_size: int) -> Iterable[List[str]]:
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def _embed_texts(texts: List[str], batch_size: int = BATCH_SIZE) -> np.ndarray:
    """
    Returns float32 matrix: (n, EMBEDDING_DIM)
    """
    vectors: List[np.ndarray] = []
    for batch in _batched(texts, batch_size=batch_size):
        try:
            batch_vecs = local_embedding(batch)
        except Exception as e:
            raise RuntimeError(
                "Embedding request failed. Check `EMBEDDING_URL` in `embedding.py` "
                "and that the service is reachable."
            ) from e

        arr = np.asarray(batch_vecs, dtype="float32")
        if arr.ndim != 2 or arr.shape[1] != EMBEDDING_DIM:
            raise ValueError(f"Expected embeddings shape (n, {EMBEDDING_DIM}), got {arr.shape}")
        vectors.append(arr)

    if not vectors:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")

    out = np.vstack(vectors).astype("float32", copy=False)
    return out


def _normalize(vectors: np.ndarray) -> np.ndarray:
    # faiss.normalize_L2 works in-place; return for convenience.
    faiss.normalize_L2(vectors)
    return vectors


def create_index(dim: int = EMBEDDING_DIM) -> faiss.Index:
    """
    Cosine similarity via Inner Product on L2-normalized vectors.
    Use ID map so we can store custom ids.
    """
    base = faiss.IndexFlatIP(dim)
    return faiss.IndexIDMap2(base)

def load_meta(meta_path: str) -> Dict[int, str]:
    if not os.path.exists(meta_path):
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # stored as { "123": "text", ... }
    return {int(k): str(v) for k, v in raw.items()}


def save_meta(meta_path: str, meta: Dict[int, str]) -> None:
    os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in meta.items()}, f, ensure_ascii=False, indent=2)


def add_texts(
    index: faiss.Index,
    meta: Dict[int, str],
    texts: List[str],
) -> Tuple[faiss.Index, Dict[int, str]]:
    if not texts:
        return index, meta

    vectors = _embed_texts(texts)
    _normalize(vectors)

    start_id = (max(meta.keys()) + 1) if meta else 0
    ids = np.arange(start_id, start_id + len(texts)).astype("int64")

    index.add_with_ids(vectors, ids)
    for i, t in zip(ids.tolist(), texts):
        meta[i] = t

    return index, meta


def search(
    index: faiss.Index,
    meta: Dict[int, str],
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> List[Dict[str, object]]:
    q_vec = _embed_texts([query])
    _normalize(q_vec)

    scores, ids = index.search(q_vec, top_k)
    out: List[Dict[str, object]] = []
    for score, _id in zip(scores[0].tolist(), ids[0].tolist()):
        if _id == -1:
            continue
        out.append({"id": int(_id), "score": float(score), "text": meta.get(int(_id), "")})
    return out


def main() -> None:
    # 0) 检查 PDF 是否存在
    if not os.path.exists(PDF_FILE_PATH):
        raise FileNotFoundError(f"PDF not found: {PDF_FILE_PATH}")

    # 1) 如果 index/meta 文件存在就直接加载，否则从 PDF 创建新的
    if os.path.exists(INDEX_FILE_PATH) and os.path.exists(META_FILE_PATH):
        print("加载已存在的 index...")
        index = faiss.read_index(INDEX_FILE_PATH)
        meta = load_meta(META_FILE_PATH)
    else:
        print("创建新的 index...")
        # PDF -> chunks
        texts = chunk_pdf_texts(PDF_FILE_PATH)
        if not texts:
            raise RuntimeError("No text chunks extracted from PDF.")

        # 创建新的 index
        index = create_index(dim=EMBEDDING_DIM)
        meta: Dict[int, str] = {}

        # embedding + add + save
        index, meta = add_texts(index=index, meta=meta, texts=texts)
        os.makedirs(OUT_DIR, exist_ok=True)
        faiss.write_index(index, INDEX_FILE_PATH)
        save_meta(META_FILE_PATH, meta)

    # 4) 查询 demo
    query = "统计语言模型"
    results = search(index=index, meta=meta, query=query, top_k=DEFAULT_TOP_K)

    print("== Build done ==")
    print(f"PDF: {PDF_FILE_PATH}")
    print(f"Index saved: {INDEX_FILE_PATH}")
    print(f"Meta saved: {META_FILE_PATH}")
    print(f"Indexed vectors: {index.ntotal}")
    print("")
    print("== Search demo ==")
    print(f"Query: {query}")
    for r in results:
        print(f"--------------------------------\n{r['text']}\n")


if __name__ == "__main__":
    main()