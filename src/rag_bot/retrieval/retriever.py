"""
Hybrid retriever: BM25 keyword search + ChromaDB vector search, merged with RRF.
"""

import time
import re
from typing import List, Dict, Tuple, Optional

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from pathlib import Path

from rag_bot.config import CHROMA_DB_DIR, EMBED_MODEL_NAME, COLLECTION_NAME


# Module-level singletons
embedder = SentenceTransformer(EMBED_MODEL_NAME)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = chroma_client.get_or_create_collection(COLLECTION_NAME)


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return re.findall(r'\w+', text.lower())


def _build_bm25_index():
    """Build a BM25 index over all documents in ChromaDB."""
    all_data = collection.get(include=["documents", "metadatas"])
    docs = all_data.get("documents", [])
    metas = all_data.get("metadatas", [])
    ids = all_data.get("ids", [])
    if not docs:
        return None, [], [], []
    tokenized = [_tokenize(d) for d in docs]
    bm25 = BM25Okapi(tokenized)
    return bm25, docs, metas, ids


def retrieve_vector(query: str, top_k: int = 10) -> List[Dict]:
    """Vector search via ChromaDB embeddings."""
    query_embedding = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
            "source": "vector"
        })
    return hits


def retrieve_bm25(query: str, top_k: int = 10) -> List[Dict]:
    """BM25 keyword search over all documents."""
    bm25, docs, metas, ids = _build_bm25_index()
    if bm25 is None:
        return []
    tokenized_query = _tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # Get top-k indices
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    hits = []
    for idx in ranked_indices:
        if scores[idx] > 0:
            hits.append({
                "id": ids[idx],
                "document": docs[idx],
                "metadata": metas[idx],
                "bm25_score": float(scores[idx]),
                "source": "bm25"
            })
    return hits


def reciprocal_rank_fusion(
    vector_hits: List[Dict],
    bm25_hits: List[Dict],
    k: int = 60,
    top_k: int = 5
) -> List[Dict]:
    """Merge results using Reciprocal Rank Fusion (RRF)."""
    scores = {}
    doc_map = {}

    # Score vector results
    for rank, hit in enumerate(vector_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = hit

    # Score BM25 results
    for rank, hit in enumerate(bm25_hits):
        doc_id = hit["id"]
        scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        if doc_id not in doc_map:
            doc_map[doc_id] = hit

    # Sort by RRF score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]

    return [doc_map[doc_id] for doc_id in sorted_ids]


def hybrid_retrieve(query: str, top_k: int = 5) -> Tuple[List[str], List[Dict]]:
    """
    Hybrid retrieval: combines vector and BM25 search with RRF.
    Returns (context_chunks, metadatas).
    """
    t0 = time.time()

    vector_hits = retrieve_vector(query, top_k=top_k * 2)
    bm25_hits = retrieve_bm25(query, top_k=top_k * 2)
    merged = reciprocal_rank_fusion(vector_hits, bm25_hits, top_k=top_k)

    print(f"[Timing] Hybrid retrieval: {time.time() - t0:.3f}s "
          f"(vector={len(vector_hits)}, bm25={len(bm25_hits)}, merged={len(merged)})")

    if not merged:
        return [], []

    context_chunks = [hit["document"] for hit in merged]
    metadatas = [hit["metadata"] for hit in merged]
    return context_chunks, metadatas


def retrieve_by_vendor(query: str, vendor: str, top_k: int = 5) -> Tuple[List[str], List[Dict]]:
    """Retrieve documents filtered to a specific vendor."""
    query_embedding = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"vendor": vendor},
        include=["documents", "metadatas", "distances"]
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    return documents, metadatas


def get_collection():
    """Return the ChromaDB collection for external use."""
    return collection


def get_embedder():
    """Return the embedding model for external use."""
    return embedder


def reload_collection():
    """Reload the ChromaDB collection (after adding new docs)."""
    global collection
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    return collection
