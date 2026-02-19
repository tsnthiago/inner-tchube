"""Integration test: runs all functions with real videos."""

from . import config  # noqa: F401 - load .env

from .get_transcript import get_transcript
from .get_metadata import get_metadata
from .get_channel_from_video import get_channel_from_video
from .search import search
from .get_channel_videos import get_channel_videos
from .get_comments import get_comments

VIDEO_URL = "https://www.youtube.com/watch?v=uDtH2mnY3nU"
VIDEO_ID = "uDtH2mnY3nU"
CHANNEL_ID = "UCiLAQS_MCw2sQQ9lQk1hA2w"  # from video
CHANNEL_HANDLER = "@alcenicorrea"
SEARCH_QUERY = "arctic monkeys"


def run():
    print("=" * 60)
    print("1. get_transcript")
    print("=" * 60)
    try:
        segments = get_transcript(VIDEO_URL)
        for s in segments[:3]:
            print(f"  [{s['start_ms']}ms] {s['text'][:60]}...")
        print(f"  ... ({len(segments)} segments total)")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("2. get_metadata")
    print("=" * 60)
    try:
        meta = get_metadata(VIDEO_URL)
        for k, v in meta.items():
            if isinstance(v, str) and len(v) > 60:
                v = v[:60] + "..."
            elif isinstance(v, list) and len(v) > 3:
                v = str(v[:3]) + "..."
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("3. get_channel_from_video")
    print("=" * 60)
    try:
        channel = get_channel_from_video(VIDEO_URL)
        for k, v in channel.items():
            print(f"  {k}: {v}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("4. search")
    print("=" * 60)
    try:
        result = search(SEARCH_QUERY, type="video")
        for item in result["items"][:3]:
            extra = f" ({item.get('video_count', '')})" if item.get("video_count") else ""
            print(f"  [{item['type']}] {item['id']} - {item['title']}{extra}")
        print(f"  ... ({len(result['items'])} items, continuation={result['continuation'] is not None})")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("5. get_channel_videos (by ID and @handle)")
    print("=" * 60)
    try:
        result = get_channel_videos(CHANNEL_ID)
        for item in result["items"][:3]:
            print(f"  [{item['video_id']}] {item['title'][:50]}...")
        print(f"  ... ({len(result['items'])} items, continuation={result['continuation'] is not None})")
        result2 = get_channel_videos(CHANNEL_HANDLER)
        print(f"  @handle OK: {len(result2['items'])} items")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("6. get_comments")
    print("=" * 60)
    try:
        result = get_comments(VIDEO_URL)
        for item in result["items"][:3]:
            print(f"  [{item['autor']}] {item.get('likes', '')}")
            print(f"    {item['texto'][:60]}...")
        print(f"  ... ({len(result['items'])} items, continuation={result['continuation'] is not None})")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print("Done")
    print("=" * 60)


if __name__ == "__main__":
    run()
