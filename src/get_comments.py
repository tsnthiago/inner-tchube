"""YouTube video comments via innertube library."""

import argparse
import re
import sys

from .config import INNERTUBE_CLIENT, INNERTUBE_CLIENT_VERSION
from innertube import InnerTube

COMMENTS_SECTION = "engagement-panel-comments-section"
SORT_ALIASES = {"Top": ("Top", "Top comments"), "Newest": ("Newest", "Newest first")}


def _video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if len(s) == 11 and s.replace("_", "").replace("-", "").isalnum():
        return s
    m = re.search(r"(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})", s)
    if m:
        return m.group(1)
    raise ValueError(f"Invalid URL or ID: {url_or_id}")


def _parse_text(obj: dict) -> str:
    if not obj:
        return ""
    runs = obj.get("runs", [])
    return "".join(r.get("text", "") for r in runs)


def _extract_token_from_engagement(next_data: dict, sort: str) -> str | None:
    titles = SORT_ALIASES.get(sort, (sort,))
    panels = next_data.get("engagementPanels", [])
    for p in panels:
        ep = p.get("engagementPanelSectionListRenderer", {})
        if ep.get("targetId") != COMMENTS_SECTION:
            continue
        header = ep.get("header", {}).get("engagementPanelTitleHeaderRenderer", {})
        menu = header.get("menu", {}).get("sortFilterSubMenuRenderer", {}).get("subMenuItems", [])
        for mi in menu:
            if mi.get("title") in titles:
                return mi.get("serviceEndpoint", {}).get("continuationCommand", {}).get("token")
    return None


def _extract_token_from_contents(next_data: dict) -> str | None:
    wnr = next_data.get("contents", {}).get("twoColumnWatchNextResults", {}).get("results", {}).get("results", {})
    for c in wnr.get("contents", []):
        isr = c.get("itemSectionRenderer", {})
        if isr.get("sectionIdentifier") != "comment-item-section":
            continue
        items = isr.get("contents", [])
        for item in items:
            cir = item.get("continuationItemRenderer", {})
            if cir:
                return cir.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
    return None


def _build_entity_map(data: dict) -> dict[str, dict]:
    out = {}
    mutations = data.get("frameworkUpdates", {}).get("entityBatchUpdate", {}).get("mutations", [])
    for m in mutations:
        cep = m.get("payload", {}).get("commentEntityPayload", {})
        if cep and cep.get("key"):
            out[cep["key"]] = cep
    return out


def _parse_comment(thread: dict, entity_map: dict | None = None) -> dict | None:
    ctr = thread.get("commentThreadRenderer", thread)
    comment_wrapper = ctr.get("comment", {}) or ctr
    cr = comment_wrapper.get("commentRenderer", {})

    if cr:
        autor = cr.get("authorText", {}).get("simpleText", "") or _parse_text(cr.get("authorText", {}))
        texto = _parse_text(cr.get("contentText", {}))
        likes = cr.get("voteCount", {}).get("simpleText", "") or cr.get("likeCount", "") or ""
        return {"autor": autor, "texto": texto, "likes": likes}

    cvm = comment_wrapper.get("commentViewModel", {}) or ctr.get("commentViewModel", {})
    inner = cvm.get("commentViewModel", cvm) if isinstance(cvm, dict) else {}
    comment_key = inner.get("commentKey") if inner else None

    if entity_map and comment_key and comment_key in entity_map:
        cep = entity_map[comment_key]
        props, author, toolbar = cep.get("properties", {}), cep.get("author", {}), cep.get("toolbar", {})
        content = props.get("content", {})
        texto = content.get("content", "") if isinstance(content, dict) else str(content or "")
        autor = author.get("displayName", "") if isinstance(author, dict) else ""
        likes = toolbar.get("likeCountLiked", "") or toolbar.get("likeCountNotliked", "") or ""
        return {"autor": autor, "texto": texto, "likes": likes}
    return None


def get_comments(url_or_id: str, sort: str = "top", continuation: str | None = None) -> dict:
    """Returns video comments. sort: top|newest."""
    video_id = _video_id(url_or_id)
    client = InnerTube(INNERTUBE_CLIENT, INNERTUBE_CLIENT_VERSION)
    sort_title = "Newest" if sort.lower() == "newest" else "Top"

    if continuation:
        data = client.next(continuation=continuation)
    else:
        next_data = client.next(video_id)
        token = _extract_token_from_engagement(next_data, sort_title) or _extract_token_from_contents(next_data)
        if not token:
            return {"items": [], "continuation": None}
        data = client.next(continuation=token)

    entity_map = _build_entity_map(data)
    items = []
    cont_token = None

    for ep in data.get("onResponseReceivedEndpoints", []):
        cont_items = ep.get("reloadContinuationItemsCommand", {}).get("continuationItems") or ep.get("appendContinuationItemsAction", {}).get("continuationItems", [])
        for ci in cont_items:
            if "commentThreadRenderer" in ci:
                parsed = _parse_comment({"commentThreadRenderer": ci["commentThreadRenderer"]}, entity_map)
                if parsed:
                    items.append(parsed)
            elif "continuationItemRenderer" in ci:
                cir = ci["continuationItemRenderer"]
                cont_token = cir.get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")

    return {"items": items, "continuation": cont_token}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url_or_id", help="Video URL or ID")
    parser.add_argument("-s", "--sort", choices=["top", "newest"], default="top")
    args = parser.parse_args()
    try:
        result = get_comments(args.url_or_id, sort=args.sort)
        for item in result["items"]:
            print(f"[{item['autor']}] {item.get('likes', '')}")
            print(item["texto"])
            print()
    except (ValueError, Exception) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
