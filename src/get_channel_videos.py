"""YouTube channel videos via innertube library."""

import argparse
import re
import sys

from .config import INNERTUBE_CLIENT, INNERTUBE_CLIENT_VERSION
from innertube import InnerTube


def _channel_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if s.startswith("UC") and len(s) == 24 and s[2:].replace("_", "").replace("-", "").replace(".", "").isalnum():
        return s
    m = re.search(r"(?:youtube\.com/channel/|/channel/)(UC[a-zA-Z0-9_-]{22})", s)
    if m:
        return m.group(1)
    raise ValueError(f"Invalid channel URL or ID: {url_or_id}")


def get_channel_videos(channel_id: str, continuation: str | None = None) -> dict:
    """Returns channel videos. Accepts channel ID (UC...) or channel URL."""
    cid = _channel_id(channel_id)
    client = InnerTube(INNERTUBE_CLIENT, INNERTUBE_CLIENT_VERSION)

    if continuation:
        data = client.browse(continuation=continuation)
        contents = data.get("onResponseReceivedActions", [{}])[0].get("appendContinuationItemsAction", {}).get("continuationItems", [])
    else:
        channel_data = client.browse(cid)
        tabs = channel_data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
        videos_tab = None
        for t in tabs:
            tr = t.get("tabRenderer", {})
            if tr.get("title") == "Videos":
                videos_tab = tr
                break
        if not videos_tab:
            return {"items": [], "continuation": None}
        params = videos_tab.get("endpoint", {}).get("browseEndpoint", {}).get("params")
        if not params:
            return {"items": [], "continuation": None}
        videos_data = client.browse(cid, params=params)
        rg = videos_data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [{}])[1].get("tabRenderer", {}).get("content", {}).get("richGridRenderer", {})
        contents = rg.get("contents", [])

    items = []
    continuation_item = {}
    for c in contents:
        if "continuationItemRenderer" in c:
            continuation_item = c
            continue
        vr = c.get("richItemRenderer", {}).get("content", {}).get("videoRenderer", {})
        if vr.get("videoId"):
            runs = vr.get("title", {}).get("runs", [])
            title = runs[0].get("text", "") if runs else ""
            items.append({"video_id": vr.get("videoId", ""), "title": title})

    cont_token = None
    cir = continuation_item.get("continuationItemRenderer", {})
    if cir:
        cont_token = cir.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

    return {"items": items, "continuation": cont_token}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("channel", help="Channel ID (UC...) or URL")
    args = parser.parse_args()
    try:
        for item in get_channel_videos(args.channel)["items"]:
            print(f"[{item['video_id']}] {item['title']}")
    except (ValueError, Exception) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
