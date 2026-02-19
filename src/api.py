"""FastAPI wrapper for InnerTube functions."""

from contextlib import asynccontextmanager
from pathlib import Path

from . import config  # noqa: F401 - load .env

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")


@app.get("/transcript")
def transcript(url_or_id: str = Query(..., description="Video URL or ID")):
    try:
        data = load_or_process_video(url_or_id)
        return data.get("transcript") or []
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load video: {e}")


@app.get("/metadata")
def metadata(url_or_id: str = Query(..., description="Video URL or ID")):
    try:
        data = load_or_process_video(url_or_id)
        return data.get("metadata") or {}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load video: {e}")


@app.get("/channel-from-video")
def channel_from_video(url_or_id: str = Query(..., description="Video URL or ID")):
    try:
        return get_channel_from_video(url_or_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get channel: {e}")


@app.get("/search")
def search_endpoint(
    q: str | None = Query(None, description="Search query (required when no continuation)"),
    type: str = Query("video", description="video|channel|playlist|film"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    if not continuation and not (q and q.strip()):
        raise HTTPException(status_code=400, detail="Provide query (q) or continuation")
    try:
        return search(q or "", type=type, continuation=continuation)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search failed: {e}")


@app.get("/channel-videos")
def channel_videos(
    channel_id: str = Query(..., description="Channel ID or URL"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    try:
        return get_channel_videos(channel_id, continuation=continuation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get channel videos: {e}")


@app.get("/comments")
def comments(
    url_or_id: str = Query(..., description="Video URL or ID"),
    sort: str = Query("top", description="top|newest"),
    continuation: str | None = Query(None, description="Continuation token"),
):
    from .get_comments import get_comments

    try:
        return get_comments(url_or_id, sort=sort, continuation=continuation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to get comments: {e}")


@app.get("/analyze-transcript")
def analyze_transcript_endpoint(
    url_or_id: str = Query(..., description="Video URL or ID"),
    prompt: str = Query(..., description="Instruction for Gemini (e.g. Summarize this video)"),
    model: str | None = Query(None, description="Gemini model override"),
):
    try:
        return analyze_transcript(url_or_id, prompt, model=model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analysis failed: {e}")


@app.get("/process")
def process_get(
    videos: str | None = Query(None, description="Comma-separated video IDs or URLs"),
    channels: str | None = Query(None, description="Comma-separated channel IDs or URLs"),
    max_videos: int = Query(20, description="Max videos to process per channel (default 20)"),
):
    """Process videos/channels, save to output/. Skips existing."""
    video_list = [v.strip() for v in (videos or "").split(",") if v.strip()]
    channel_list = [c.strip() for c in (channels or "").split(",") if c.strip()]
    if not video_list and not channel_list:
        raise HTTPException(status_code=400, detail="Provide videos and/or channels")
    return process_items(
        videos=video_list,
        channels=channel_list,
        max_videos_per_channel=max_videos,
    )


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
    """Query uses same dimension as stored vectors (from collection)."""

    query: str
    top_k: int = 5
    video_id: str | None = None


@app.post("/semantic-similarity")
def semantic_similarity_endpoint(body: SemanticSimilarityBody):
    """Compute cosine similarity matrix for texts."""
    if len(body.texts) < 2:
        return {"similarity_matrix": [[1.0]] if body.texts else [], "texts": body.texts}
    try:
        return semantic_similarity(body.texts, body.output_dimensionality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Semantic similarity failed: {e}")


@app.post("/classify")
def classify_endpoint(body: ClassifyBody):
    """Classify texts to nearest label by embedding similarity."""
    if not body.texts or not body.labels:
        raise HTTPException(status_code=400, detail="Provide texts and labels")
    try:
        return classify(body.texts, body.labels, body.output_dimensionality)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Classification failed: {e}")


@app.post("/cluster")
def cluster_endpoint(body: ClusterBody):
    """Cluster texts using KMeans on embeddings."""
    if not body.texts or body.n_clusters < 2:
        raise HTTPException(status_code=400, detail="Provide texts and n_clusters >= 2")
    try:
        return cluster(
            body.texts,
            body.n_clusters,
            body.output_dimensionality,
            body.random_state,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Clustering failed: {e}")


@app.post("/search-videos")
def search_videos_endpoint(body: SearchVideosBody):
    """Semantic search over video chunks in Qdrant. Query embedding uses same dimension as stored vectors."""
    from .embeddings import create_embeddings

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Provide query")

    output_dimensionality = get_collection_vector_size()
    if output_dimensionality is None:
        raise HTTPException(
            status_code=503,
            detail="No video chunks in Qdrant. Index at least one video with POST /embeddings first.",
        )

    try:
        result = create_embeddings(
            texts=[body.query],
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=output_dimensionality,
            normalize=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    query_vector = result["embeddings"][0]
    try:
        hits = qdrant_search(
            query_vector=query_vector,
            limit=body.top_k,
            video_id=body.video_id,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant search failed: {e}")

    return {
        "query": body.query,
        "top_k": body.top_k,
        "results": hits,
    }


@app.post("/semantic-search")
def semantic_search_endpoint(body: SemanticSearchBody):
    """Search corpus for texts most similar to query."""
    if not body.corpus:
        raise HTTPException(status_code=400, detail="Provide corpus")
    try:
        return semantic_search(
            body.query,
            body.corpus,
            body.top_k,
            body.output_dimensionality,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Semantic search failed: {e}")


@app.post("/embeddings")
def embeddings_endpoint(body: EmbeddingsBody):
    """Load/process video, generate embeddings from transcript, save to Qdrant. Skips if already in Qdrant."""
    from .get_metadata import _video_id

    try:
        vid = _video_id(body.video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
        raise HTTPException(status_code=503, detail=f"Qdrant check failed: {e}")

    try:
        data = load_or_process_video(body.video_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to load video: {e}")

    transcript = data.get("transcript")
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not available for this video")

    texts = [s["text"] for s in transcript if s.get("text")]
    if not texts:
        raise HTTPException(status_code=404, detail="No transcript text to embed")

    try:
        result = create_embeddings(
            texts=texts,
            task_type=body.task_type,
            output_dimensionality=body.output_dimensionality,
            normalize=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embeddings failed: {e}")

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
        raise HTTPException(status_code=503, detail=f"Qdrant upsert failed: {e}")

    return {
        "video_id": vid,
        "chunks_upserted": count,
        "collection": "video_chunks",
    }


class ProcessBody(BaseModel):
    videos: list[str] | None = None
    channels: list[str] | None = None
    max_videos: int = 20


@app.post("/process")
def process_post(body: ProcessBody):
    """Process videos/channels from JSON body. Keys: videos, channels (arrays), max_videos (default 20)."""
    video_list = body.videos or []
    channel_list = body.channels or []
    if not video_list and not channel_list:
        raise HTTPException(status_code=400, detail="Provide videos and/or channels in body")
    return process_items(
        videos=video_list,
        channels=channel_list,
        max_videos_per_channel=body.max_videos,
    )
