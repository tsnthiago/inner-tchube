"""
InnerTube API - Busca e Transcript (legendas) do YouTube.
Usa requests diretamente, sem a biblioteca innertube.
"""

import html
import re
import xml.etree.ElementTree as ET

import requests

BASE_URL = "https://youtubei.googleapis.com/youtubei/v1"
API_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
CLIENT_VERSION = "2.20250626.01.00"

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

# ANDROID: necessário para player retornar captionTracks
ANDROID_API_KEY = "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w"
ANDROID_CLIENT = {"clientName": "ANDROID", "clientVersion": "20.10.38"}


def _request(
    endpoint: str, body: dict, video_id: str | None = None, visitor_id: str | None = None
) -> dict:
    url = f"{BASE_URL}/{endpoint}?key={API_KEY}&prettyPrint=false"
    headers = dict(HEADERS)
    if video_id:
        headers["Referer"] = f"https://www.youtube.com/watch?v={video_id}"
    if visitor_id:
        headers["X-Goog-Visitor-Id"] = visitor_id
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def search(query: str) -> dict:
    """Busca vídeos no YouTube."""
    body = {"context": {"client": CONTEXT["client"]}, "query": query}
    return _request("search", body)


def get_transcript(video_id: str, lang: str | None = None) -> list[dict]:
    """
    Obtém o transcript (legendas) de um vídeo.
    Usa o endpoint player (ANDROID) -> captionTracks -> baseUrl (XML).
    Retorna lista de {text, start_ms}.
    """
    # Passo 1: player com cliente ANDROID (retorna captionTracks)
    player_body = {"context": {"client": ANDROID_CLIENT}, "videoId": video_id}
    url = f"{BASE_URL}/player?key={ANDROID_API_KEY}&prettyPrint=false"
    headers = dict(HEADERS)
    headers["Referer"] = f"https://www.youtube.com/watch?v={video_id}"
    resp = requests.post(url, json=player_body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    captions = (
        data.get("captions", {})
        .get("playerCaptionsTracklistRenderer", {})
        .get("captionTracks", [])
    )
    if not captions:
        raise ValueError("Transcript não encontrado ou indisponível para este vídeo.")

    # Escolher track por idioma ou primeiro disponível
    track = None
    if lang:
        for t in captions:
            if t.get("languageCode") == lang:
                track = t
                break
    if not track:
        track = captions[0]

    base_url = track.get("baseUrl")
    if not base_url:
        raise ValueError("URL do transcript não encontrada.")

    # Remover parâmetro fmt se presente (retorna XML limpo)
    base_url = re.sub(r"&fmt=\w+$", "", base_url)

    # Passo 2: buscar XML e parsear
    headers = dict(HEADERS)
    headers["Referer"] = f"https://www.youtube.com/watch?v={video_id}"
    resp = requests.get(base_url, headers=headers, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    segments = []
    # YouTube XML: <transcript><text start="..." dur="...">...</text></transcript>
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag != "text":
            continue
        text = (elem.text or "") + "".join((child.tail or "") for child in elem)
        text = html.unescape(text.replace("\n", " ").strip())

        start = float(elem.get("start", 0))
        start_ms = int(start * 1000)

        segments.append({"text": text, "start_ms": start_ms})

    return segments


if __name__ == "__main__":
    # Exemplo: busca
    print("=== Busca: innertube api python ===")
    result = search("innertube api python")
    print(f"Resultado: {len(result.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', []))} seções")

    # Exemplo: transcript (vídeo conhecido com legendas)
    video_id = "dQw4w9WgXcQ"
    print(f"\n=== Transcript: {video_id} ===")
    try:
        segments = get_transcript(video_id)
        for s in segments[:5]:
            print(f"  [{s.get('start_ms', '?')}ms] {s['text'][:60]}...")
        if len(segments) > 5:
            print(f"  ... e mais {len(segments) - 5} segmentos")
    except (ValueError, requests.RequestException) as e:
        print(f"  Erro: {e}")
