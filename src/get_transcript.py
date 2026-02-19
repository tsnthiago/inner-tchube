"""YouTube video transcripts via InnerTube API."""

import html
import re
import sys
import xml.etree.ElementTree as ET

import requests

from .config import ANDROID_API_KEY, ANDROID_VERSION, BASE_URL, CLIENT_VERSION, TIMEOUT

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
    "Referer": "https://www.youtube.com/",
    "X-Goog-Api-Format-Version": "1",
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": CLIENT_VERSION,
    "Origin": "https://www.youtube.com",
}
ANDROID_CLIENT = {"clientName": "ANDROID", "clientVersion": ANDROID_VERSION}


def get_transcript(url_or_id: str) -> list[dict]:
    """Returns transcript (prefers auto-generated). Accepts video URL or ID."""
    video_id = _video_id(url_or_id)
    tracks = _fetch_caption_tracks(video_id)
    track = next((t for t in tracks if t.get("kind") == "asr"), tracks[0])
    base_url = re.sub(r"&fmt=\w+$", "", track.get("baseUrl", ""))
    if not base_url:
        raise ValueError("Transcript not available for this video.")

    r = requests.get(
        base_url,
        headers={**HEADERS, "Referer": f"https://www.youtube.com/watch?v={video_id}"},
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


def _video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if len(s) == 11 and s.replace("_", "").replace("-", "").isalnum():
        return s
    m = re.search(r"(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)
    raise ValueError(f"Invalid URL or ID: {url_or_id}")


def _fetch_caption_tracks(video_id: str) -> list:
    r = requests.post(
        f"{BASE_URL}/player?key={ANDROID_API_KEY}&prettyPrint=false",
        json={"context": {"client": ANDROID_CLIENT}, "videoId": video_id},
        headers={**HEADERS, "Referer": f"https://www.youtube.com/watch?v={video_id}"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    tracks = r.json().get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    if not tracks:
        raise ValueError("Transcript not available for this video.")
    return tracks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.get_transcript <url or video id>")
        sys.exit(1)
    try:
        for s in get_transcript(sys.argv[1]):
            print(s["text"])
    except (ValueError, requests.RequestException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
