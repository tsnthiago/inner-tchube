"""YouTube video transcripts via innertube library."""

import html
import re
import sys
import xml.etree.ElementTree as ET

import requests

from config import INNERTUBE_CLIENT, INNERTUBE_CLIENT_VERSION, TIMEOUT

try:
    import innertube
except ImportError:
    innertube = None


def get_transcript(url_or_id: str) -> list[dict]:
    """
    Returns transcript (prefers auto-generated captions).
    Accepts video URL or ID.
    Returns: [{"text": str, "start_ms": int}, ...]
    """
    video_id = _video_id(url_or_id)

    if innertube is None:
        return _fallback_transcript(video_id)

    try:
        client = innertube.InnerTube("ANDROID", INNERTUBE_CLIENT_VERSION)
        data = client.player(video_id)
        tracks = data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    except Exception:
        return _fallback_transcript(video_id)

    if not tracks:
        return _fallback_transcript(video_id)

    track = next((t for t in tracks if t.get("kind") == "asr"), tracks[0])
    base_url = re.sub(r"&fmt=\w+$", "", track.get("baseUrl", ""))
    if not base_url:
        raise ValueError("Transcript not available for this video.")

    r = requests.get(
        base_url,
        headers={"Referer": f"https://www.youtube.com/watch?v={video_id}"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()

    segments = []
    for elem in ET.fromstring(r.text).iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag != "text":
            continue
        text = (elem.text or "") + "".join((c.tail or "") for c in elem)
        text = html.unescape(text.replace("\n", " ").strip())
        segments.append({"text": text, "start_ms": int(float(elem.get("start", 0)) * 1000)})
    return segments


def _fallback_transcript(video_id: str) -> list[dict]:
    from get_transcript import get_transcript as _get
    return _get(video_id)


def _video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if len(s) == 11 and s.replace("_", "").replace("-", "").isalnum():
        return s
    m = re.search(r"(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)
    raise ValueError(f"Invalid URL or ID: {url_or_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_transcript_lib.py <url or video id>")
        sys.exit(1)
    try:
        for s in get_transcript(sys.argv[1]):
            print(s["text"])
    except (ValueError, requests.RequestException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
