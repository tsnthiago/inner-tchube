"""Process videos and channels, save to output/."""

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import TIMEOUT_CHANNEL
from .get_metadata import get_metadata, _video_id
from .get_transcript import get_transcript
from .get_comments import get_comments
from .get_channel_from_video import get_channel_from_video
from .get_channel_videos import get_channel_videos, _channel_id

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
VIDEOS_DIR = OUTPUT_DIR / "videos"
CHANNELS_DIR = OUTPUT_DIR / "channels"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def process_video(video_id: str, timeout: int | None = None) -> dict:
    """Fetch metadata, transcript, comments for a video. Returns aggregated dict."""
    metadata = get_metadata(video_id, timeout=timeout)

    transcript = None
    try:
        transcript = get_transcript(video_id)
    except Exception:
        pass

    comments_data = get_comments(video_id, sort="top")
    comments = comments_data.get("items", []) or []

    return {
        "metadata": metadata,
        "transcript": transcript,
        "comments": comments,
    }


def save_video_json(video_id: str, data: dict) -> Path:
    """Save video data to output/videos/{video_id}.json."""
    _ensure_dir(VIDEOS_DIR)
    path = VIDEOS_DIR / f"{video_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def load_or_process_video(video_id: str) -> dict:
    """Carrega de output/videos/{id}.json se existir; senão processa, salva e retorna."""
    vid = _video_id(video_id)
    path = VIDEOS_DIR / f"{vid}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    data = process_video(vid)
    save_video_json(vid, data)
    return data


def save_channel_json(channel_id: str, data: dict) -> Path:
    """Save channel data to output/channels/{channel_id}.json."""
    _ensure_dir(CHANNELS_DIR)
    path = CHANNELS_DIR / f"{channel_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _get_channel_videos(channel_id: str, max_videos: int = 20) -> list[dict]:
    """Fetch videos from a channel with pagination, limited to max_videos."""
    all_items = []
    result = get_channel_videos(channel_id)
    all_items.extend(result["items"])
    while result.get("continuation") and len(all_items) < max_videos:
        result = get_channel_videos(channel_id, continuation=result["continuation"])
        all_items.extend(result["items"])
    return all_items[:max_videos]


def process_channel(channel_id: str, max_videos: int = 20) -> dict:
    """Process channel: get videos (up to max_videos), process new ones, save channel JSON."""
    cid = _channel_id(channel_id)
    all_videos = _get_channel_videos(cid, max_videos=max_videos)
    video_ids = [v["video_id"] for v in all_videos]

    channel_info = None
    newly_processed = []

    for item in all_videos:
        vid = item["video_id"]
        video_path = VIDEOS_DIR / f"{vid}.json"
        if video_path.exists():
            continue
        try:
            data = process_video(vid, timeout=TIMEOUT_CHANNEL)
            save_video_json(vid, data)
            newly_processed.append(vid)
            if not channel_info and data.get("metadata"):
                meta = data["metadata"]
                channel_info = {
                    "canal_id": meta.get("canal_id", cid),
                    "nome": meta.get("autor", ""),
                    "url_canal": meta.get("url_canal", f"https://www.youtube.com/channel/{cid}"),
                }
        except Exception:
            pass

    if not channel_info:
        try:
            first_video = all_videos[0]["video_id"] if all_videos else None
            if first_video:
                channel_info = get_channel_from_video(first_video)
            else:
                channel_info = {"canal_id": cid, "nome": "", "url_canal": f"https://www.youtube.com/channel/{cid}"}
        except Exception:
            channel_info = {"canal_id": cid, "nome": "", "url_canal": f"https://www.youtube.com/channel/{cid}"}

    channel_data = {
        **channel_info,
        "video_ids": video_ids,
        "last_processed": datetime.now(timezone.utc).isoformat(),
    }
    save_channel_json(cid, channel_data)

    return {"channel_id": cid, "newly_processed": newly_processed, "total_videos": len(video_ids)}


def _normalize_video_id(raw: str) -> str | None:
    try:
        return _video_id(raw)
    except ValueError:
        return None


def _normalize_channel_id(raw: str) -> str | None:
    try:
        return _channel_id(raw)
    except ValueError:
        return None


def process_items(
    videos: list[str] | None = None,
    channels: list[str] | None = None,
    max_videos_per_channel: int = 20,
) -> dict:
    """Process videos and channels, skip existing. Returns summary.
    max_videos_per_channel: limit of videos to fetch/process per channel (default 20)."""
    videos = videos or []
    channels = channels or []

    processed = []
    skipped = []
    errors = []

    for raw in videos:
        vid = _normalize_video_id(raw)
        if not vid:
            errors.append({"input": raw, "error": "Invalid video ID or URL"})
            continue
        video_path = VIDEOS_DIR / f"{vid}.json"
        if video_path.exists():
            skipped.append(vid)
            continue
        try:
            data = process_video(vid)
            save_video_json(vid, data)
            processed.append(vid)
        except Exception as e:
            errors.append({"input": raw, "error": str(e)})

    for raw in channels:
        cid = _normalize_channel_id(raw)
        if not cid:
            errors.append({"input": raw, "error": "Invalid channel ID or URL"})
            continue
        try:
            result = process_channel(cid, max_videos=max_videos_per_channel)
            processed.append(f"channel:{cid}")
            processed.extend(result.get("newly_processed", []))
        except Exception as e:
            errors.append({"input": raw, "error": str(e)})

    return {
        "processed": processed,
        "skipped": skipped,
        "errors": errors,
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "error_count": len(errors),
    }
