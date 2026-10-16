
import faiss
import numpy as np


def build_vector_store(embeddings):
    """
    Build a FAISS index from normalized text embeddings.
    """
    embeddings = np.asarray(embeddings, dtype=np.float32)

    if embeddings.ndim != 2 or embeddings.shape[0] == 0:
        raise ValueError("Embeddings must be a non-empty 2D array.")

    if embeddings.shape[1] == 0:
        raise ValueError("Embeddings must have at least one dimension.")

    # Inner product gives cosine similarity for normalized vectors.
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return index


def search_vector_store(index, query_embedding, chunks, top_k=3):
    """
    Find the most relevant text chunks for a query embedding.
    """
    query_embedding = np.asarray(
        query_embedding, dtype=np.float32
    )

    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    if query_embedding.ndim != 2 or query_embedding.shape[0] != 1:
        raise ValueError("Provide exactly one query embedding.")

    if query_embedding.shape[1] != index.d:
        raise ValueError("Query embedding dimension does not match index.")

    if index.ntotal != len(chunks):
        raise ValueError("The number of chunks must match the index.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    if index.ntotal == 0:
        return []

    top_k = min(top_k, index.ntotal)
    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx >= 0:
            results.append({
                "chunk": chunks[int(idx)],
                "score": float(score)
            })

    return results
