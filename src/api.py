"""FastAPI wrapper for InnerTube functions."""

from contextlib import asynccontextmanager

from . import config  # noqa: F401 - load .env

from fastapi import FastAPI, Query
from pydantic import BaseModel

from .get_transcript import get_transcript
from .get_metadata import get_metadata
from .get_channel_from_video import get_channel_from_video
from .search import search
from .get_channel_videos import get_channel_videos
from .get_comments import get_comments
from .analyze_transcript import analyze_transcript
from .embeddings import create_embeddings
from .semantic import semantic_similarity, classify, cluster, semantic_search
from .process import process_items
from .scheduler import start_scheduler

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
    return get_transcript(url_or_id)


@app.get("/metadata")
def metadata(url_or_id: str = Query(..., description="Video URL or ID")):
    return get_metadata(url_or_id)


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
    return get_comments(url_or_id, sort=sort, continuation=continuation)


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
    text: str | None = None
    texts: list[str] | None = None
    task_type: str = "RETRIEVAL_DOCUMENT"
    output_dimensionality: int = 3072
    normalize: bool | None = None


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
    """Generate embeddings using gemini-embedding-001. Requires text or texts."""
    if body.text is not None and body.texts is not None:
        return {"error": "Provide either text or texts, not both"}
    if body.text is None and (body.texts is None or len(body.texts) == 0):
        return {"error": "Provide text or texts"}
    texts = [body.text] if body.text is not None else body.texts
    return create_embeddings(
        texts=texts,
        task_type=body.task_type,
        output_dimensionality=body.output_dimensionality,
        normalize=body.normalize,
    )


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
