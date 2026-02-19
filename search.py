"""YouTube search via innertube library."""

import argparse
import sys

from innertube import InnerTube

TYPE_PARAMS = {"video": "EgIQAQ%3D%3D", "channel": "EgIQAg%3D%3D", "playlist": "EgIQAw%3D%3D", "film": "EgIQBA%3D%3D"}


def _title_from_runs(obj: dict) -> str:
    return (obj.get("title", {}).get("runs", [{}])[0].get("text", "")) if obj.get("title") else ""


def search(query: str, type: str = "video", continuation: str | None = None) -> dict:
    """
    Returns search results. type: video|channel|playlist|film.
    Returns: {"items": [...], "continuation": str|None}
    """
    client = InnerTube("WEB")
    if continuation:
        data = client.search(continuation=continuation)
    else:
        params = TYPE_PARAMS.get(type.lower(), TYPE_PARAMS["video"])
        data = client.search(query, params=params)

    if "contents" in data:
        slr = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]
        contents = slr["contents"]
    elif "onResponseReceivedCommands" in data:
        contents = data["onResponseReceivedCommands"][0]["appendContinuationItemsAction"]["continuationItems"]
    else:
        return {"items": [], "continuation": None}

    item_section = contents[0] if contents else {}
    continuation_item = contents[-1] if len(contents) > 1 else {}
    results = item_section.get("itemSectionRenderer", {}).get("contents", [])
    items = []
    for r in results:
        key = next(iter(r), None)
        if not key:
            continue
        val = r[key]
        if key == "videoRenderer":
            items.append({"type": "video", "id": val.get("videoId", ""), "title": _title_from_runs(val)})
        elif key == "channelRenderer":
            items.append({"type": "channel", "id": val.get("channelId", ""), "title": val.get("title", {}).get("simpleText", "")})
        elif key == "playlistRenderer":
            items.append({"type": "playlist", "id": val.get("playlistId", ""), "title": val.get("title", {}).get("simpleText", ""), "video_count": val.get("videoCount", "")})
        elif key in ("shelfRenderer", "reelShelfRenderer"):
            for c in val.get("content", {}).get("horizontalListRenderer", {}).get("items", []):
                vr = c.get("gridVideoRenderer") or c.get("videoRenderer", {})
                if vr.get("videoId"):
                    items.append({"type": "video", "id": vr.get("videoId", ""), "title": _title_from_runs(vr)})

    cont_token = None
    cir = continuation_item.get("continuationItemRenderer", {})
    if cir:
        cont_token = cir.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

    return {"items": items, "continuation": cont_token}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Search query")
    parser.add_argument("-t", "--type", choices=["video", "channel", "playlist", "film"], default="video")
    args = parser.parse_args()
    try:
        result = search(args.query, type=args.type)
        for item in result["items"]:
            extra = f" ({item.get('video_count', '')})" if item.get("video_count") else ""
            print(f"[{item['type']}] {item['id']} - {item['title']}{extra}")
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
