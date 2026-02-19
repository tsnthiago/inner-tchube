"""Qdrant store for video embeddings."""

import hashlib
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, MatchValue

from .config import QDRANT_URL

COLLECTION_NAME = "video_chunks"
DEFAULT_VECTOR_SIZE = 768


def _get_client() -> QdrantClient:
    """Get Qdrant client. Raises if Qdrant is unreachable."""
    return QdrantClient(url=QDRANT_URL)


def _point_id(video_id: str, segment_idx: int) -> int:
    """Deterministic int64 ID for Qdrant point."""
    s = f"{video_id}_{segment_idx}"
    return int(hashlib.md5(s.encode()).hexdigest()[:16], 16)


def video_chunks_exist(video_id: str) -> bool:
    """Return True if any chunks for this video_id exist in Qdrant."""
    client = _get_client()
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        return False
    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
        ),
        exact=True,
    )
    return result.count > 0


def ensure_collection(vector_size: int = DEFAULT_VECTOR_SIZE) -> None:
    """Create collection if it does not exist."""
    client = _get_client()
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    if COLLECTION_NAME not in names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_video_chunks(
    video_id: str,
    embeddings: list[list[float]],
    payloads: list[dict[str, Any]],
) -> int:
    """Upsert video chunks to Qdrant. Returns count of points upserted."""
    if len(embeddings) != len(payloads):
        raise ValueError("embeddings and payloads must have same length")
    if not embeddings:
        return 0

    client = _get_client()
    vector_size = len(embeddings[0])
    ensure_collection(vector_size)

    points = [
        PointStruct(
            id=_point_id(video_id, i),
            vector=emb,
            payload=payloads[i],
        )
        for i, emb in enumerate(embeddings)
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search(
    query_vector: list[float],
    limit: int = 5,
    video_id: str | None = None,
) -> list[dict[str, Any]]:
    """Search video chunks by query vector. Returns hits with payload."""
    client = _get_client()
    collections = client.get_collections().collections
    if COLLECTION_NAME not in [c.name for c in collections]:
        return []

    query_filter = None
    if video_id:
        query_filter = Filter(
            must=[FieldCondition(key="video_id", match=MatchValue(value=video_id))]
        )

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        query_filter=query_filter,
    )

    hits = []
    for p in result.points:
        hits.append({
            "score": p.score,
            "payload": p.payload or {},
        })
    return hits
