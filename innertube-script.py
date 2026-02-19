"""
InnerTube API - Transcript de vídeos do YouTube.
"""

import argparse
import html
import re
import sys
import xml.etree.ElementTree as ET

import requests

# --- Parâmetros configuráveis ---
BASE_URL = "https://youtubei.googleapis.com/youtubei/v1"
API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
ANDROID_API_KEY = "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"
CLIENT_VERSION = "2.20250626.01.00"
ANDROID_VERSION = "20.10.38"
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

CONTEXT = {
    "client": {
        "clientName": "WEB",
        "clientVersion": CLIENT_VERSION,
        "hl": "pt",
        "gl": "BR",
    }
}
ANDROID_CLIENT = {"clientName": "ANDROID", "clientVersion": ANDROID_VERSION}


def _extract_video_id(url_or_id: str) -> str:
    if len(url_or_id) == 11 and url_or_id.replace("_", "").replace("-", "").isalnum():
        return url_or_id
    m = re.search(r"(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    raise ValueError(f"URL ou ID inválido: {url_or_id}")


def get_transcript(video_id: str, lang: str | None = None, prefer_auto: bool = True) -> list[dict]:
    r = requests.post(
        f"{BASE_URL}/player?key={ANDROID_API_KEY}&prettyPrint=false",
        json={"context": {"client": ANDROID_CLIENT}, "videoId": video_id},
        headers={**HEADERS, "Referer": f"https://www.youtube.com/watch?v={video_id}"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    tracks = r.json().get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    if not tracks:
        raise ValueError("Transcript não disponível para este vídeo.")

    track = None
    if prefer_auto:
        for t in tracks:
            if t.get("kind") == "asr":
                track = t
                break
    if not track and lang:
        for t in tracks:
            if t.get("languageCode") == lang:
                track = t
                break
    if not track:
        track = tracks[0]

    base_url = re.sub(r"&fmt=\w+$", "", track.get("baseUrl", ""))
    if not base_url:
        raise ValueError("URL do transcript não encontrada.")

    resp = requests.get(
        base_url,
        headers={**HEADERS, "Referer": f"https://www.youtube.com/watch?v={video_id}"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    segments = []
    for elem in ET.fromstring(resp.text).iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag != "text":
            continue
        text = (elem.text or "") + "".join((c.tail or "") for c in elem)
        text = html.unescape(text.replace("\n", " ").strip())
        segments.append({"text": text, "start_ms": int(float(elem.get("start", 0)) * 1000)})

    return segments


def search(query: str) -> dict:
    r = requests.post(
        f"{BASE_URL}/search?key={API_KEY}&prettyPrint=false",
        json={"context": {"client": CONTEXT["client"]}, "query": query},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obter transcript de vídeo YouTube")
    parser.add_argument("url", nargs="?", help="URL ou ID do vídeo")
    parser.add_argument("-l", "--lang", help="Código do idioma (ex: en, pt)")
    parser.add_argument("--no-auto", action="store_true", help="Não preferir legendas auto-geradas")
    args = parser.parse_args()

    if not args.url:
        parser.print_help()
        sys.exit(1)

    try:
        video_id = _extract_video_id(args.url)
        segments = get_transcript(video_id, lang=args.lang, prefer_auto=not args.no_auto)
        for s in segments:
            print(s["text"])
    except (ValueError, requests.RequestException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
