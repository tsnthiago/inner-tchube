"""YouTube video metadata via InnerTube API."""

import re
import sys

import requests

BASE_URL = "https://youtubei.googleapis.com/youtubei/v1"
API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
CLIENT_VERSION = "2.20250626.01.00"
TIMEOUT = 30

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
    "Referer": "https://www.youtube.com/",
    "X-Goog-Api-Format-Version": "1",
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": CLIENT_VERSION,
    "Origin": "https://www.youtube.com",
}
CONTEXT = {"client": {"clientName": "WEB", "clientVersion": CLIENT_VERSION, "hl": "pt", "gl": "BR"}}


def get_metadata(url_or_id: str) -> dict:
    """Returns video metadata. Accepts URL or ID."""
    video_id = _video_id(url_or_id)
    ref = f"https://www.youtube.com/watch?v={video_id}"
    h = {**HEADERS, "Referer": ref}

    player = requests.post(f"{BASE_URL}/player?key={API_KEY}", json={"context": CONTEXT, "videoId": video_id}, headers=h, timeout=TIMEOUT).json()
    next_data = requests.post(f"{BASE_URL}/next?key={API_KEY}", json={"context": CONTEXT, "videoId": video_id}, headers=h, timeout=TIMEOUT).json()

    vd = player.get("videoDetails", {}) or {}
    mf = player.get("microformat", {}).get("playerMicroformatRenderer", {}) or {}
    contents = next_data.get("contents", {}).get("twoColumnWatchNextResults", {}).get("results", {}).get("results", {}).get("contents", [])

    likes, data_pub = None, None
    for item in contents:
        if "videoPrimaryInfoRenderer" not in item:
            continue
        vpi = item["videoPrimaryInfoRenderer"]
        data_pub = vpi.get("dateText", {}).get("simpleText")
        try:
            b = vpi.get("videoActions", {}).get("menuRenderer", {}).get("topLevelButtons", [{}])[0]
            b = b.get("segmentedLikeDislikeButtonViewModel", {}).get("likeButtonViewModel", {}).get("likeButtonViewModel", {})
            b = b.get("toggleButtonViewModel", {}).get("toggleButtonViewModel", {}).get("defaultButtonViewModel", {}).get("buttonViewModel", {})
            likes = b.get("title")
        except (IndexError, KeyError, TypeError):
            pass
        break

    thumbs = vd.get("thumbnail", {}).get("thumbnails", [])
    thumb_url = max(thumbs, key=lambda t: t.get("width", 0)).get("url") if thumbs else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    return {
        "video_id": video_id,
        "titulo": vd.get("title", ""),
        "views": vd.get("viewCount", ""),
        "duracao_segundos": int(vd.get("lengthSeconds", 0) or 0),
        "autor": vd.get("author", ""),
        "canal_id": vd.get("channelId", ""),
        "url_canal": mf.get("ownerProfileUrl", ""),
        "descricao": vd.get("shortDescription", ""),
        "likes": likes,
        "data_publicacao": data_pub,
        "data_publicacao_iso": mf.get("publishDate", ""),
        "categoria": mf.get("category", ""),
        "keywords": vd.get("keywords", []),
        "thumbnail_url": thumb_url,
        "embed_url": mf.get("embed", {}).get("iframeUrl", f"https://www.youtube.com/embed/{video_id}"),
        "is_live": vd.get("isLiveContent", False),
    }


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
        print("Usage: python get_metadata.py <url or video id>")
        sys.exit(1)
    try:
        for k, v in get_metadata(sys.argv[1]).items():
            if isinstance(v, str) and len(v) > 80:
                v = v[:80] + "..."
            elif isinstance(v, list) and len(v) > 5:
                v = str(v[:5]) + "..."
            print(f"{k}: {v}")
    except (ValueError, requests.RequestException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
