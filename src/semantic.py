"""Semantic operations: similarity, classification, clustering, search."""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

from .embeddings import create_embeddings


def _get_embeddings(texts: list[str], task_type: str, dim: int = 768) -> np.ndarray:
    """Get normalized embeddings as numpy array."""
    result = create_embeddings(
        texts=texts,
        task_type=task_type,
        output_dimensionality=dim,
        normalize=True,
    )
    return np.array(result["embeddings"], dtype=np.float32)


def semantic_similarity(texts: list[str], output_dimensionality: int = 768) -> dict:
    """Compute cosine similarity matrix for texts. Uses SEMANTIC_SIMILARITY."""
    if len(texts) < 2:
        return {"similarity_matrix": [[1.0]] if texts else [], "texts": texts}
    emb = _get_embeddings(texts, "SEMANTIC_SIMILARITY", output_dimensionality)
    sim = cosine_similarity(emb)
    return {
        "similarity_matrix": sim.tolist(),
        "texts": texts,
    }


def classify(texts: list[str], labels: list[str], output_dimensionality: int = 768) -> dict:
    """Classify each text to nearest label by cosine similarity. Uses CLASSIFICATION."""
    if not texts or not labels:
        return {"classifications": [], "texts": texts, "labels": labels}
    text_emb = _get_embeddings(texts, "CLASSIFICATION", output_dimensionality)
    label_emb = _get_embeddings(labels, "CLASSIFICATION", output_dimensionality)
    sim = cosine_similarity(text_emb, label_emb)
    classifications = []
    for i, text in enumerate(texts):
        best_idx = int(np.argmax(sim[i]))
        classifications.append({
            "text": text,
            "label": labels[best_idx],
            "score": float(sim[i][best_idx]),
        })
    return {
        "classifications": classifications,
        "texts": texts,
        "labels": labels,
    }


def cluster(
    texts: list[str],
    n_clusters: int,
    output_dimensionality: int = 768,
    random_state: int = 42,
) -> dict:
    """Cluster texts using KMeans on embeddings. Uses CLUSTERING."""
    if not texts or n_clusters < 2:
        return {"clusters": [], "texts": texts, "n_clusters": n_clusters}
    n_clusters = min(n_clusters, len(texts))
    emb = _get_embeddings(texts, "CLUSTERING", output_dimensionality)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    labels = kmeans.fit_predict(emb)
    clusters = [
        {"text": text, "cluster_id": int(lbl)}
        for text, lbl in zip(texts, labels)
    ]
    return {
        "clusters": clusters,
        "texts": texts,
        "n_clusters": n_clusters,
    }


def semantic_search(
    query: str,
    corpus: list[str],
    top_k: int = 5,
    output_dimensionality: int = 768,
) -> dict:
    """Search corpus for texts most similar to query. Uses RETRIEVAL_QUERY + RETRIEVAL_DOCUMENT."""
    if not corpus:
        return {"results": [], "query": query, "corpus": corpus}
    query_emb = _get_embeddings([query], "RETRIEVAL_QUERY", output_dimensionality)
    doc_emb = _get_embeddings(corpus, "RETRIEVAL_DOCUMENT", output_dimensionality)
    sim = cosine_similarity(query_emb, doc_emb)[0]
    top_indices = np.argsort(sim)[::-1][:top_k]
    results = [
        {"text": corpus[i], "score": float(sim[i]), "rank": r + 1}
        for r, i in enumerate(top_indices)
    ]
    return {
        "results": results,
        "query": query,
        "top_k": top_k,
    }
