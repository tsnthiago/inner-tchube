"""YouTube channel info from video via InnerTube API."""

import sys

import requests

from .config import BASE_URL, CLIENT_VERSION, METADATA_GL, METADATA_HL, TIMEOUT, WEB_API_KEY
from .get_metadata import _video_id

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
    "Referer": "https://www.youtube.com/",
    "X-Goog-Api-Format-Version": "1",
    "X-YouTube-Client-Name": "1",
    "X-YouTube-Client-Version": CLIENT_VERSION,
    "Origin": "https://www.youtube.com",
}
CONTEXT = {"client": {"clientName": "WEB", "clientVersion": CLIENT_VERSION, "hl": METADATA_HL, "gl": METADATA_GL}}


def get_channel_from_video(url_or_id: str) -> dict:
    """Returns channel info from a video. Accepts URL or video ID."""
    video_id = _video_id(url_or_id)
    ref = f"https://www.youtube.com/watch?v={video_id}"
    h = {**HEADERS, "Referer": ref}

    player = requests.post(
        f"{BASE_URL}/player?key={WEB_API_KEY}",
        json={"context": CONTEXT, "videoId": video_id},
        headers=h,
        timeout=TIMEOUT,
    ).json()

    vd = player.get("videoDetails", {}) or {}
    mf = player.get("microformat", {}).get("playerMicroformatRenderer", {}) or {}

    canal_id = vd.get("channelId", "")
    url_canal = mf.get("ownerProfileUrl", "")
    if not url_canal and canal_id:
        url_canal = f"https://www.youtube.com/channel/{canal_id}"

    return {
        "canal_id": canal_id,
        "nome": vd.get("author", ""),
        "url_canal": url_canal,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.get_channel_from_video <url or video id>")
        sys.exit(1)
    try:
        for k, v in get_channel_from_video(sys.argv[1]).items():
            print(f"{k}: {v}")
    except (ValueError, requests.RequestException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
