"""
embeddings.py — Embedding-based retrieval for the secondary knowledge base.

Each chunk (from chunker.py) gets embedded once and cached to disk, so a
large source (e.g. a 350-page book) is only ever embedded a single time,
not on every generation run. At generation time, the post's "angle" text
is embedded once, and chunks are ranked by cosine similarity to it — so
only the most relevant few chunks make it into the prompt, regardless of
how large the overall secondary KB grows.

Uses OpenAI's text-embedding-3-small (cheap, small vectors) via the same
client already configured in llm_integration.py.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from src.llm_integration import client

EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_CACHE_PATH = Path("knowledge_base/secondary/.embeddings_cache.json")


def _chunk_key(chunk) -> str:
    """Stable cache key: identifies this exact chunk's content, so an edit
    to a source file naturally invalidates only the changed chunks."""
    text_hash = hashlib.sha1(chunk.text.encode("utf-8")).hexdigest()[:12]
    return f"{chunk.doc_id}:{chunk.chunk_index}:{text_hash}"


def _load_cache(cache_path: Path) -> dict:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache_path: Path, cache: dict) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache), encoding="utf-8")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts in one API call."""
    if not texts:
        return []
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def get_chunk_embeddings(chunks: list, cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, list[float]]:
    """Return {chunk_key: embedding} for every given chunk, computing and
    caching only the ones not already cached."""
    cache = _load_cache(cache_path)

    missing_keys = []
    missing_texts = []
    for chunk in chunks:
        key = _chunk_key(chunk)
        if key not in cache:
            missing_keys.append(key)
            missing_texts.append(chunk.text)

    if missing_texts:
        new_embeddings = embed_texts(missing_texts)
        for key, embedding in zip(missing_keys, new_embeddings):
            cache[key] = embedding
        _save_cache(cache_path, cache)

    return {_chunk_key(chunk): cache[_chunk_key(chunk)] for chunk in chunks}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr, b_arr = np.array(a), np.array(b)
    denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if denom == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / denom)


def retrieve_top_chunks(
    chunks: list,
    query: str,
    top_k: int = 6,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> list:
    """Rank the given chunks by similarity to the query text and return
    the top_k most relevant ones. Assumes chunks are already pre-filtered
    (e.g. by topic) by the caller."""
    if not chunks or not query.strip():
        return chunks[:top_k]

    chunk_embeddings = get_chunk_embeddings(chunks, cache_path)
    query_embedding = embed_texts([query])[0]

    scored = [
        (cosine_similarity(query_embedding, chunk_embeddings[_chunk_key(chunk)]), chunk)
        for chunk in chunks
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]
