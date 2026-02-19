# InnerTube – YouTube Transcript & Metadata

A minimal Python project that fetches YouTube video transcripts and metadata using the **InnerTube API**—YouTube's internal, undocumented API that powers the website. No official API key or quota limits required.

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Project Structure](#project-structure)
6. [Implementation Guide](#implementation-guide)
7. [API Reference](#api-reference)
8. [Recreating the Project](#recreating-the-project)

---

## Overview

This project provides two standalone modules:

| Module | Purpose |
|--------|---------|
| `get_transcript.py` | Fetches video captions/transcripts (prefers auto-generated) |
| `get_metadata.py` | Fetches video metadata (title, views, likes, thumbnail, etc.) |

Both use direct HTTP requests to `youtubei.googleapis.com` with publicly available API keys. No authentication or Google Cloud setup is needed.

---

## Requirements

- **Python 3.10+**
- **requests** (single dependency)

---

## Installation

```bash
pip install -r requirements.txt
```

Or:

```bash
pip install requests
```

---

## Usage

### As a Library

```python
from get_transcript import get_transcript
from get_metadata import get_metadata

# Transcript (returns list of {text, start_ms})
segments = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
for s in segments:
    print(s["text"])

# Metadata (returns dict)
meta = get_metadata("dQw4w9WgXcQ")
print(meta["titulo"], meta["views"], meta["thumbnail_url"])
```

### Command Line

```bash
# Transcript (prints text line by line)
python get_transcript.py https://youtube.com/watch?v=dQw4w9WgXcQ
python get_transcript.py dQw4w9WgXcQ

# Metadata (prints all fields)
python get_metadata.py dQw4w9WgXcQ
```

Both functions accept:
- Full URLs: `https://www.youtube.com/watch?v=VIDEO_ID`, `https://youtu.be/VIDEO_ID`, `https://youtube.com/embed/VIDEO_ID`
- Raw video ID: `dQw4w9WgXcQ` (11 characters)

---

## Project Structure

```
innertube/
├── get_transcript.py   # Transcript fetcher
├── get_metadata.py     # Metadata fetcher
├── requirements.txt    # requests
└── README.md
```

---

## Implementation Guide

### What is the InnerTube API?

InnerTube is YouTube's internal JSON API. It returns structured data (often "renderers") used to build the UI. Unlike the public YouTube Data API v3, it:

- Has no official quota
- Uses public API keys embedded in the YouTube frontend
- Returns raw, presentation-oriented JSON that requires parsing

### Base Configuration (Shared)

All requests use:

- **Base URL:** `https://youtubei.googleapis.com/youtubei/v1`
- **Headers:**
  - `Content-Type: application/json`
  - `User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36`
  - `Referer: https://www.youtube.com/` (or `https://www.youtube.com/watch?v={video_id}` for video-specific calls)
  - `X-Goog-Api-Format-Version: 1`
  - `X-YouTube-Client-Name: 1`
  - `X-YouTube-Client-Version: 2.20250626.01.00`
  - `Origin: https://www.youtube.com`

### Video ID Extraction

Both modules extract the 11-character video ID from URLs or raw IDs:

- Direct ID: 11 alphanumeric chars (with `_` and `-` allowed)
- Regex: `(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})`

---

## API Reference

### get_transcript.py

**Flow:**

1. **Player endpoint (ANDROID client)**  
   - URL: `POST {BASE_URL}/player?key={ANDROID_API_KEY}&prettyPrint=false`  
   - Body: `{"context": {"client": {"clientName": "ANDROID", "clientVersion": "20.10.38"}}, "videoId": "{video_id}"}`  
   - API Key: `AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w`  
   - The WEB client does not return `captionTracks`; ANDROID does.

2. **Extract caption track**  
   - Path: `response.captions.playerCaptionsTracklistRenderer.captionTracks`  
   - Prefer track with `kind == "asr"` (auto-generated). Fallback: first track.  
   - Each track has `baseUrl` (URL to XML captions).

3. **Fetch XML**  
   - GET the `baseUrl` (optionally strip `&fmt=...` for plain XML).  
   - Parse `<transcript><text start="..." dur="...">...</text></transcript>`  
   - Decode HTML entities (`&#39;` → `'`).

4. **Return**  
   - List of `{"text": str, "start_ms": int}`.

**Dependencies:** `html`, `re`, `sys`, `xml.etree.ElementTree`, `requests`

---

### get_metadata.py

**Flow:**

1. **Player endpoint (WEB client)**  
   - URL: `POST {BASE_URL}/player?key={API_KEY}`  
   - Body: `{"context": {"client": {"clientName": "WEB", "clientVersion": "2.20250626.01.00", "hl": "pt", "gl": "BR"}}, "videoId": "{video_id}"}`  
   - API Key: `AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8`

2. **Next endpoint (WEB client)**  
   - URL: `POST {BASE_URL}/next?key={API_KEY}`  
   - Body: same context + `videoId`  
   - Provides likes and human-readable publish date.

3. **Extract fields**

   **From `player.videoDetails`:**
   - `title`, `viewCount`, `lengthSeconds`, `author`, `channelId`, `shortDescription`
   - `thumbnail.thumbnails` (list of `{url, width, height}`)
   - `keywords` (list of strings)
   - `isLiveContent` (boolean)

   **From `player.microformat.playerMicroformatRenderer`:**
   - `publishDate` (ISO 8601)
   - `category`, `ownerProfileUrl`
   - `embed.iframeUrl`

   **From `next.contents.twoColumnWatchNextResults.results.results.contents`:**
   - Find `videoPrimaryInfoRenderer`
   - `dateText.simpleText` → human-readable publish date
   - Likes path: `videoActions.menuRenderer.topLevelButtons[0].segmentedLikeDislikeButtonViewModel.likeButtonViewModel.likeButtonViewModel.toggleButtonViewModel.toggleButtonViewModel.defaultButtonViewModel.buttonViewModel.title`

4. **Thumbnail**  
   - Use the thumbnail with the largest `width` from `videoDetails.thumbnail.thumbnails`.  
   - Fallback: `https://i.ytimg.com/vi/{video_id}/hqdefault.jpg`

5. **Return**  
   - Dict with: `video_id`, `titulo`, `views`, `duracao_segundos`, `autor`, `canal_id`, `url_canal`, `descricao`, `likes`, `data_publicacao`, `data_publicacao_iso`, `categoria`, `keywords`, `thumbnail_url`, `embed_url`, `is_live`

**Dependencies:** `re`, `sys`, `requests`

---

## Recreating the Project

### Step 1: Project Setup

```bash
mkdir innertube && cd innertube
```

Create `requirements.txt`:

```
requests
```

### Step 2: get_transcript.py

Create a file with:

1. **Constants:** `BASE_URL`, `ANDROID_API_KEY`, `CLIENT_VERSION`, `ANDROID_VERSION`, `TIMEOUT`, `HEADERS`, `ANDROID_CLIENT`
2. **`_video_id(url_or_id)`** – extract 11-char ID from URL or raw ID
3. **`_fetch_caption_tracks(video_id)`** – POST to `/player` with ANDROID context, return `captionTracks`
4. **`get_transcript(url_or_id)`** – pick ASR track or first, GET XML from `baseUrl`, parse `<text>` elements, return `[{text, start_ms}]`
5. **`if __name__ == "__main__"`** – CLI: print each segment’s text

Key implementation details:
- Use `ANDROID` client for player (WEB does not return captions)
- Prefer `kind == "asr"` for auto-generated captions
- XML: iterate `root.iter()`, filter `tag == "text"`, use `elem.get("start")`, `html.unescape()` for text

### Step 3: get_metadata.py

Create a file with:

1. **Constants:** `BASE_URL`, `API_KEY`, `CLIENT_VERSION`, `TIMEOUT`, `HEADERS`, `CONTEXT` (WEB client)
2. **`_video_id(url_or_id)`** – same logic as transcript
3. **`get_metadata(url_or_id)`** – call `/player` and `/next`, extract all fields as described in API Reference
4. **`if __name__ == "__main__"`** – CLI: print each metadata field

Key implementation details:
- Use WEB client for both endpoints
- Likes require traversing the nested path in `videoPrimaryInfoRenderer`
- Thumbnail: `max(thumbnails, key=lambda t: t.get("width", 0))`

### Step 4: Verify

```bash
pip install requests
python get_transcript.py dQw4w9WgXcQ
python get_metadata.py dQw4w9WgXcQ
```

---

## API Keys (Public)

| Client | API Key | Use |
|--------|---------|-----|
| WEB | `AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8` | Metadata (player, next) |
| ANDROID | `AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w` | Transcript (player returns captionTracks) |

These keys are embedded in YouTube’s frontend and are publicly known.

---

## Limitations

- **Transcript:** Only works for videos with captions (manual or auto-generated). Auto-generated (`asr`) is preferred when available.
- **Metadata:** Structure can change if YouTube updates InnerTube. The likes path in particular is fragile.
- **Rate limiting:** No official limits, but excessive requests may trigger blocks.
- **Comments:** Not implemented; the current InnerTube comment structure uses `commentViewModel` instead of `commentRenderer`, which would require additional parsing.

---

## License

Use at your own risk. This project is not affiliated with YouTube or Google.
