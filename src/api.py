"""FastAPI wrapper for InnerTube functions."""

from . import config  # noqa: F401 - load .env

from fastapi import FastAPI, Query

from .get_transcript import get_transcript
from .get_metadata import get_metadata
from .get_channel_from_video import get_channel_from_video
from .search import search
from .get_channel_videos import get_channel_videos
from .get_comments import get_comments
from .analyze_transcript import analyze_transcript

app = FastAPI(title="InnerTube API")


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
