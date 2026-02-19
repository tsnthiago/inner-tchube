"""FastAPI wrapper for InnerTube functions."""

from contextlib import asynccontextmanager

from . import config  # noqa: F401 - load .env

from fastapi import FastAPI, Query
from pydantic import BaseModel

from .get_channel_from_video import get_channel_from_video
from .search import search
from .get_channel_videos import get_channel_videos
from .analyze_transcript import analyze_transcript
from .embeddings import create_embeddings
from .semantic import semantic_similarity, classify, cluster, semantic_search
from .process import process_items, load_or_process_video
from .scheduler import start_scheduler
from .qdrant_store import upsert_video_chunks, search as qdrant_search, video_chunks_exist, get_collection_vector_size

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    _scheduler = start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="InnerTube API", lifespan=lifespan)


@app.get("/transcript")
def transcript(url_or_id: str = Query(..., description="Video URL or ID")):
    data = load_or_process_video(url_or_id)
    return data.get("transcript") or []


@app.get("/metadata")
def metadata(url_or_id: str = Query(..., description="Video URL or ID")):
    data = load_or_process_video(url_or_id)
    return data.get("metadata") or {}


@app.get("/channel-from-video")
def channel_from_video(url_or_id: str = Query(..., description="Video URL or ID")):
    return get_channel_from_video(url_or_id)


@app.get("/search")
def search_endpoint(
    q: str = Query(..., description="Search query"),
    type: str = Query("video", description="video|channel|playlist|film"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    return search(q, type=type, continuation=continuation)


@app.get("/channel-videos")
def channel_videos(
    channel_id: str = Query(..., description="Channel ID or URL"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    return get_channel_videos(channel_id, continuation=continuation)


@app.get("/comments")
def comments(
    url_or_id: str = Query(..., description="Video URL or ID"),
    sort: str = Query("top", description="top|newest"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    from .get_comments import get_comments

    if continuation:
        return get_comments(url_or_id, sort=sort, continuation=continuation)
    data = load_or_process_video(url_or_id)
    items = data.get("comments") or []
    return {"items": items, "continuation": None}


@app.get("/analyze-transcript")
def analyze_transcript_endpoint(
    url_or_id: str = Query(..., description="Video URL or ID"),
    prompt: str = Query(..., description="Instruction for Gemini (e.g. Summarize this video)"),
    model: str | None = Query(None, description="Gemini model override"),
):
    return analyze_transcript(url_or_id, prompt, model=model)


@app.get("/process")
def process_get(
    videos: str | None = Query(None, description="Comma-separated video IDs or URLs"),
    channels: str | None = Query(None, description="Comma-separated channel IDs or URLs"),
):
    """Process videos/channels, save to output/. Skips existing."""
    video_list = [v.strip() for v in (videos or "").split(",") if v.strip()]
    channel_list = [c.strip() for c in (channels or "").split(",") if c.strip()]
    if not video_list and not channel_list:
        return {"error": "Provide videos and/or channels"}
    return process_items(videos=video_list, channels=channel_list)


class EmbeddingsBody(BaseModel):
    video_id: str
    task_type: str = "RETRIEVAL_DOCUMENT"
    output_dimensionality: int = 768


class SemanticSimilarityBody(BaseModel):
    texts: list[str]
    output_dimensionality: int = 768


class ClassifyBody(BaseModel):
    texts: list[str]
    labels: list[str]
    output_dimensionality: int = 768


class ClusterBody(BaseModel):
    texts: list[str]
    n_clusters: int
    output_dimensionality: int = 768
    random_state: int = 42


class SemanticSearchBody(BaseModel):
    query: str
    corpus: list[str]
    top_k: int = 5
    output_dimensionality: int = 768


class SearchVideosBody(BaseModel):
    query: str
    top_k: int = 5
    video_id: str | None = None
    output_dimensionality: int = 768


@app.post("/semantic-similarity")
def semantic_similarity_endpoint(body: SemanticSimilarityBody):
    """Compute cosine similarity matrix for texts."""
    if len(body.texts) < 2:
        return {"similarity_matrix": [[1.0]] if body.texts else [], "texts": body.texts}
    return semantic_similarity(body.texts, body.output_dimensionality)


@app.post("/classify")
def classify_endpoint(body: ClassifyBody):
    """Classify texts to nearest label by embedding similarity."""
    if not body.texts or not body.labels:
        return {"error": "Provide texts and labels"}
    return classify(body.texts, body.labels, body.output_dimensionality)


@app.post("/cluster")
def cluster_endpoint(body: ClusterBody):
    """Cluster texts using KMeans on embeddings."""
    if not body.texts or body.n_clusters < 2:
        return {"error": "Provide texts and n_clusters >= 2"}
    return cluster(
        body.texts,
        body.n_clusters,
        body.output_dimensionality,
        body.random_state,
    )


@app.post("/search-videos")
def search_videos_endpoint(body: SearchVideosBody):
    """Semantic search over video chunks in Qdrant. Query embedding uses same dimension as stored vectors."""
    from .embeddings import create_embeddings

    if not body.query.strip():
        return {"error": "Provide query"}

    output_dimensionality = get_collection_vector_size()
    if output_dimensionality is None:
        return {"error": "No video chunks in Qdrant. Index at least one video with POST /embeddings first."}

    try:
        result = create_embeddings(
            texts=[body.query],
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=output_dimensionality,
            normalize=True,
        )
    except ValueError as e:
        return {"error": str(e)}

    query_vector = result["embeddings"][0]
    try:
        hits = qdrant_search(
            query_vector=query_vector,
            limit=body.top_k,
            video_id=body.video_id,
        )
    except Exception as e:
        return {"error": f"Qdrant search failed: {e}"}

    return {
        "query": body.query,
        "top_k": body.top_k,
        "results": hits,
    }


@app.post("/semantic-search")
def semantic_search_endpoint(body: SemanticSearchBody):
    """Search corpus for texts most similar to query."""
    if not body.corpus:
        return {"error": "Provide corpus"}
    return semantic_search(
        body.query,
        body.corpus,
        body.top_k,
        body.output_dimensionality,
    )


@app.post("/embeddings")
def embeddings_endpoint(body: EmbeddingsBody):
    """Load/process video, generate embeddings from transcript, save to Qdrant. Skips if already in Qdrant."""
    from .get_metadata import _video_id

    try:
        vid = _video_id(body.video_id)
    except ValueError as e:
        return {"error": str(e)}

    try:
        if video_chunks_exist(vid):
            return {
                "video_id": vid,
                "chunks_upserted": 0,
                "collection": "video_chunks",
                "skipped": True,
                "reason": "Video embeddings already exist in Qdrant",
            }
    except Exception as e:
        return {"error": f"Qdrant check failed: {e}"}

    data = load_or_process_video(body.video_id)
    transcript = data.get("transcript")
    if not transcript:
        return {"error": "Transcript not available for this video"}

    texts = [s["text"] for s in transcript if s.get("text")]
    if not texts:
        return {"error": "No transcript text to embed"}

    result = create_embeddings(
        texts=texts,
        task_type=body.task_type,
        output_dimensionality=body.output_dimensionality,
        normalize=True,
    )
    embeddings = result["embeddings"]
    metadata = data.get("metadata") or {}

    payloads = [
        {
            "video_id": vid,
            "titulo": metadata.get("titulo", ""),
            "autor": metadata.get("autor", ""),
            "canal_id": metadata.get("canal_id", ""),
            "segment_text": seg["text"],
            "start_ms": seg.get("start_ms", 0),
            "thumbnail_url": metadata.get("thumbnail_url", ""),
            "views": metadata.get("views", ""),
            "duracao_segundos": metadata.get("duracao_segundos", 0),
        }
        for seg in transcript
        if seg.get("text")
    ]

    try:
        count = upsert_video_chunks(vid, embeddings, payloads)
    except Exception as e:
        return {"error": f"Qdrant upsert failed: {e}"}

    return {
        "video_id": vid,
        "chunks_upserted": count,
        "collection": "video_chunks",
    }


class ProcessBody(BaseModel):
    videos: list[str] | None = None
    channels: list[str] | None = None


@app.post("/process")
def process_post(body: ProcessBody):
    """Process videos/channels from JSON body. Keys: videos, channels (arrays)."""
    video_list = body.videos or []
    channel_list = body.channels or []
    if not video_list and not channel_list:
        return {"error": "Provide videos and/or channels in body"}
    return process_items(videos=video_list, channels=channel_list)
