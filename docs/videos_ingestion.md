"""
YouTube CSV Consolidator (raw -> cleaned events + consolidated videos + channel notifications)

Inputs (raw CSVs):
- liked.csv
- watched.csv
- history.csv
- history2.csv
- channels.csv

Outputs (final CSVs):
- youtube_events_clean_dedup.csv
- youtube_consolidated_final.csv
- youtube_consolidated_with_channel_notifs.csv

Usage:
    python youtube_consolidator.py \
        --liked liked.csv \
        --watched watched.csv \
        --history history.csv \
        --history2 history2.csv \
        --channels channels.csv \
        --outdir .

Notes:
- This script assumes your raw exports resemble the column structures you uploaded.
- It deduplicates event-level rows and then consolidates per video_id.
- It parses the "channels.csv" last column (ytLottieComponentHost href) as notifications_all if it contains "[object Object]".
"""

from __future__ import annotations

import argparse
import os
import re
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict

import numpy as np
import pandas as pd


# -----------------------------
# Helpers
# -----------------------------

def clean_text(x) -> Optional[str]:
    if pd.isna(x):
        return None
    s = str(x)
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def norm_str(x) -> Optional[str]:
    s = clean_text(x)
    if s is None:
        return None
    s = s.lower().replace("\u200b", "")
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def extract_video_id(url) -> Optional[str]:
    """Extract YouTube video ID from common URL patterns."""
    if pd.isna(url):
        return None
    s = str(url).strip()
    if not s:
        return None

    # Try to isolate a URL-like chunk
    m = re.search(r'(https?://[^\s"]+|/watch\?[^\s"]+)', s)
    if m:
        s = m.group(1)

    if s.startswith("/watch"):
        s = "https://www.youtube.com" + s

    try:
        u = urlparse(s)
        if "youtu.be" in u.netloc:
            vid = u.path.strip("/").split("/")[0]
            return vid or None

        qs = parse_qs(u.query)
        if "v" in qs:
            return qs["v"][0]

        if "/shorts/" in u.path:
            parts = u.path.split("/shorts/")
            if len(parts) > 1:
                vid = parts[1].split("/")[0]
                return vid or None
    except Exception:
        pass

    # Fallback: any 11-char pattern (imperfect, but helps)
    m2 = re.search(r"([a-zA-Z0-9_-]{11})", s)
    return m2.group(1) if m2 else None


def to_datetime_safe(x) -> pd.Timestamp:
    if pd.isna(x):
        return pd.NaT
    s = str(x).strip()
    if not s:
        return pd.NaT
    # best-effort parse
    return pd.to_datetime(s, errors="coerce", utc=True)


def parse_subscribers(s) -> float:
    """Parse '26.2K subscribers' -> 26200, '1.3M subscribers' -> 1300000."""
    if pd.isna(s):
        return np.nan
    t = str(s).lower().replace("subscribers", "").replace("subscriber", "").strip()
    m = re.match(r"([\d.,]+)\s*([km]?)", t)
    if not m:
        return np.nan
    num = m.group(1).replace(",", ".")
    try:
        val = float(num)
    except Exception:
        return np.nan
    mult = m.group(2)
    if mult == "k":
        val *= 1_000
    elif mult == "m":
        val *= 1_000_000
    return val


def first_nonnull(series: pd.Series):
    s = series.dropna()
    return s.iloc[0] if len(s) else None


def mode_nonnull(series: pd.Series):
    s = series.dropna()
    return s.value_counts().index[0] if len(s) else None


def minmax(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - mn) / (mx - mn)


def read_csv_safely(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, encoding="utf-8", errors="replace")


# -----------------------------
# Standardizers (match your raw exports)
# -----------------------------

def standardize_liked(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    # Expected columns from your liked.csv:
    # yt-simple-endpoint href (video url), ytCoreImageHost src, yt-badge-shape__text (duration),
    # yt-simple-endpoint (title), yt-simple-endpoint 2 (channel), yt-simple-endpoint href 3 (channel url),
    # style-scope 6 (views), style-scope 8 (age)
    out = pd.DataFrame({
        "source": source_name,
        "event_type": "liked",
        "video_url": df.get("yt-simple-endpoint href"),
        "thumbnail_url": df.get("ytCoreImageHost src"),
        "duration_text": df.get("yt-badge-shape__text"),
        "title": df.get("yt-simple-endpoint"),
        "channel": df.get("yt-simple-endpoint 2"),
        "channel_url": df.get("yt-simple-endpoint href 3"),
        "views_text": df.get("style-scope 6"),
        "age_text": df.get("style-scope 8"),
    })
    out["video_id"] = out["video_url"].map(extract_video_id)
    for c in out.columns:
        if c not in ("source", "event_type"):
            out[c] = out[c].map(clean_text)
    return out


def standardize_watched(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    # Expected columns from your watched.csv:
    # yt-simple-endpoint href (video url), ytCoreImageHost src, style-scope 2 (WATCHED label),
    # yt-badge-shape__text (duration), yt-simple-endpoint (title), yt-simple-endpoint 2 (channel),
    # yt-simple-endpoint href 3 (channel url), style-scope 6 (views), style-scope 8 (age)
    out = pd.DataFrame({
        "source": source_name,
        "event_type": "watched",
        "video_url": df.get("yt-simple-endpoint href"),
        "thumbnail_url": df.get("ytCoreImageHost src"),
        "watched_label": df.get("style-scope 2"),
        "duration_text": df.get("yt-badge-shape__text"),
        "title": df.get("yt-simple-endpoint"),
        "channel": df.get("yt-simple-endpoint 2"),
        "channel_url": df.get("yt-simple-endpoint href 3"),
        "views_text": df.get("style-scope 6"),
        "age_text": df.get("style-scope 8"),
    })
    out["video_id"] = out["video_url"].map(extract_video_id)
    for c in out.columns:
        if c not in ("source", "event_type"):
            out[c] = out[c].map(clean_text)
    return out


def standardize_history(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    # Expected columns from your history.csv:
    # yt-lockup-view-model__content-image href (video url), ytCoreImageHost src, yt-badge-shape__text,
    # yt-core-attributed-string (title), yt-core-attributed-string 2 (channel),
    # yt-core-attributed-string 3 (watch_time_text), yt-core-attributed-string 4 (watch_date_text)
    out = pd.DataFrame({
        "source": source_name,
        "event_type": "history",
        "video_url": df.get("yt-lockup-view-model__content-image href"),
        "thumbnail_url": df.get("ytCoreImageHost src"),
        "duration_text": df.get("yt-badge-shape__text"),
        "title": df.get("yt-core-attributed-string"),
        "channel": df.get("yt-core-attributed-string 2"),
        "watch_time_text": df.get("yt-core-attributed-string 3"),
        "watch_date_text": df.get("yt-core-attributed-string 4"),
    })
    out["video_id"] = out["video_url"].map(extract_video_id)
    for c in out.columns:
        if c not in ("source", "event_type"):
            out[c] = out[c].map(clean_text)
    out["watched_at"] = out["watch_date_text"].map(to_datetime_safe)
    return out


def standardize_history2(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    # Expected columns from your history2.csv:
    # l8sGWb href (video url), M1gnGc src (thumb), hFYxqd (title), H3Q9vf (channel)
    url_col = "l8sGWb href" if "l8sGWb href" in df.columns else (
        "l8sGWb href 2" if "l8sGWb href 2" in df.columns else (
            "SiEggd href" if "SiEggd href" in df.columns else None
        )
    )
    out = pd.DataFrame({
        "source": source_name,
        "event_type": "history",
        "video_url": df.get(url_col) if url_col else None,
        "thumbnail_url": df.get("M1gnGc src"),
        "title": df.get("hFYxqd") if "hFYxqd" in df.columns else df.get("hFYxqd 2"),
        "channel": df.get("H3Q9vf"),
        "badge": df.get("QTGV3c") if "QTGV3c" in df.columns else df.get("bI9urf"),
    })
    out["video_id"] = out["video_url"].map(extract_video_id)
    for c in out.columns:
        if c not in ("source", "event_type"):
            out[c] = out[c].map(clean_text)
    return out


# -----------------------------
# Channels normalizer
# -----------------------------

def normalize_channels(channels_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a normalized channels table, including a boolean notifications_all flag derived from:
    last column (ytLottieComponentHost href) == "[object Object]" -> True
    """
    last_col = channels_df.columns[-1]

    out = pd.DataFrame({
        "channel_url": channels_df.get("channel-link href").map(clean_text),
        "channel_name": channels_df.get("style-scope").map(clean_text),
        "channel_handle": channels_df.get("style-scope 2").map(clean_text),
        "subscribers_text": channels_df.get("style-scope 4").map(clean_text),
        "subscribers": channels_df.get("style-scope 4").map(parse_subscribers),
        "description": channels_df.get("style-scope 5").map(clean_text),
        "notif_raw": channels_df.get(last_col),
    })

    out["notifications_all"] = out["notif_raw"].astype(str).str.contains(r"\[object Object\]", na=False)

    # Normalize join keys
    out["channel_url_norm"] = out["channel_url"].str.lower()
    out["channel_name_norm"] = out["channel_name"].map(norm_str)
    out["channel_handle_norm"] = out["channel_handle"].map(clean_text)

    # Dedupe (best effort)
    out["channel_key"] = out["channel_handle_norm"].fillna(out["channel_url"]).fillna(out["channel_name_norm"])
    out = out.drop_duplicates(subset=["channel_key"]).copy()

    return out


# -----------------------------
# Pipeline
# -----------------------------

def build_events(liked: pd.DataFrame, watched: pd.DataFrame, history: pd.DataFrame, history2: pd.DataFrame) -> pd.DataFrame:
    events = pd.concat([
        standardize_liked(liked, "liked.csv"),
        standardize_watched(watched, "watched.csv"),
        standardize_history(history, "history.csv"),
        standardize_history2(history2, "history2.csv"),
    ], ignore_index=True)

    # Drop rows without video_id (key field)
    events = events[events["video_id"].notna()].copy()

    # Normalized strings for dedupe
    events["title_norm"] = events["title"].map(norm_str)
    events["channel_norm"] = events["channel"].map(norm_str)
    events["video_key"] = "id:" + events["video_id"].astype(str)

    # Deduplicate exact duplicate events
    events["event_fingerprint"] = (
        events["event_type"].fillna("") + "|" +
        events["video_key"].fillna("") + "|" +
        events["video_url"].fillna("") + "|" +
        events["title_norm"].fillna("") + "|" +
        events["channel_norm"].fillna("")
    )
    events = events.drop_duplicates(subset=["event_fingerprint"]).copy()

    return events


def consolidate_videos(events: pd.DataFrame) -> pd.DataFrame:
    g = events.groupby("video_key", dropna=False)

    def agg_mode(col: str):
        return g[col].apply(mode_nonnull).values if col in events.columns else None

    video = pd.DataFrame({
        "video_key": g.size().index,
        "video_id": agg_mode("video_id"),
        "video_url": agg_mode("video_url"),
        "title": agg_mode("title"),
        "channel": agg_mode("channel"),
        "channel_url": agg_mode("channel_url"),
        "thumbnail_url": agg_mode("thumbnail_url"),
        "views_text": agg_mode("views_text"),
        "age_text": agg_mode("age_text"),
        "duration_text": agg_mode("duration_text"),
        "events_total": g.size().values,
        "n_liked": g.apply(lambda d: (d["event_type"] == "liked").sum()).values,
        "n_watched": g.apply(lambda d: (d["event_type"] == "watched").sum()).values,
        "n_history": g.apply(lambda d: (d["event_type"] == "history").sum()).values,
    })

    video["has_liked"] = video["n_liked"] > 0
    video["has_watched"] = video["n_watched"] > 0
    video["has_history"] = video["n_history"] > 0
    video["watch_occurrences"] = video["n_watched"] + video["n_history"]

    # History timestamps when available
    if "watched_at" in events.columns:
        wt = g["watched_at"].agg(["min", "max"]).reset_index().rename(columns={"min": "watched_at_min", "max": "watched_at_max"})
        video = video.merge(wt, on="video_key", how="left")
    else:
        video["watched_at_min"] = pd.NaT
        video["watched_at_max"] = pd.NaT

    # Normalized metrics
    video["events_total_norm"] = minmax(video["events_total"])
    video["watch_occurrences_norm"] = minmax(video["watch_occurrences"])

    # Stable sort
    video = video.sort_values(["watch_occurrences", "has_liked", "events_total"], ascending=[False, False, False]).reset_index(drop=True)
    return video


def add_channel_notifications(video: pd.DataFrame, channels_norm: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      - notifications_all_flag (bool, default False if unknown)
      - notifications_all_confidence (1 if matched, 0 if unknown)
      - optional channel metadata (subscribers/subscribers_text/handle)
    """
    out = video.copy()

    # Normalize join keys
    out["channel_url_norm"] = out["channel_url"].astype(str).str.lower()
    out["channel_name_norm_l"] = out["channel"].astype(str).str.lower()

    # Merge by channel URL when available
    ch = channels_norm.copy()
    ch["channel_url_norm"] = ch["channel_url_norm"].astype(str)

    merged = out.merge(
        ch[["channel_url_norm", "notifications_all", "subscribers", "subscribers_text", "channel_handle_norm"]],
        on="channel_url_norm",
        how="left",
        suffixes=("", "_ch"),
    )

    # Fallback merge by channel name (because many videos don't have channel_url)
    ch_name = ch.dropna(subset=["channel_name_norm"]).copy()
    ch_name["channel_name_norm_l"] = ch_name["channel_name_norm"].str.lower()

    merged = merged.merge(
        ch_name[["channel_name_norm_l", "notifications_all", "subscribers", "subscribers_text", "channel_handle_norm"]],
        left_on="channel_name_norm_l",
        right_on="channel_name_norm_l",
        how="left",
        suffixes=("", "_byname"),
    )

    # Coalesce URL-match then name-match
    for col in ["notifications_all", "subscribers", "subscribers_text", "channel_handle_norm"]:
        merged[col] = merged[col].combine_first(merged[f"{col}_byname"])

    # Final flags
    merged["notifications_all_flag"] = merged["notifications_all"].fillna(False).astype(bool)
    merged["notifications_all_confidence"] = (~merged["notifications_all"].isna()).astype(int)

    # Cleanup
    drop_cols = [c for c in merged.columns if c.endswith("_byname")]
    merged = merged.drop(columns=drop_cols + ["notifications_all", "channel_name_norm_l"], errors="ignore")

    return merged


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Consolidate raw YouTube CSV exports into cleaned events and consolidated video tables.")
    parser.add_argument("--liked", required=True, help="Path to liked.csv")
    parser.add_argument("--watched", required=True, help="Path to watched.csv")
    parser.add_argument("--history", required=True, help="Path to history.csv")
    parser.add_argument("--history2", required=True, help="Path to history2.csv")
    parser.add_argument("--channels", required=True, help="Path to channels.csv")
    parser.add_argument("--outdir", default=".", help="Output directory (default: current folder)")
    args = parser.parse_args()

    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)

    liked_df = read_csv_safely(args.liked)
    watched_df = read_csv_safely(args.watched)
    history_df = read_csv_safely(args.history)
    history2_df = read_csv_safely(args.history2)
    channels_df = read_csv_safely(args.channels)

    events = build_events(liked_df, watched_df, history_df, history2_df)
    videos = consolidate_videos(events)
    channels_norm = normalize_channels(channels_df)
    videos_with_notifs = add_channel_notifications(videos, channels_norm)

    # Write outputs
    events_out = os.path.join(outdir, "youtube_events_clean_dedup.csv")
    videos_out = os.path.join(outdir, "youtube_consolidated_final.csv")
    videos_notifs_out = os.path.join(outdir, "youtube_consolidated_with_channel_notifs.csv")

    events.to_csv(events_out, index=False)
    videos.to_csv(videos_out, index=False)
    videos_with_notifs.to_csv(videos_notifs_out, index=False)

    print("Done.")
    print(f"- Events (clean + dedup): {events_out}  | rows={len(events)}")
    print(f"- Videos (consolidated):  {videos_out}  | rows={len(videos)}")
    print(f"- Videos (+notifs):       {videos_notifs_out}  | rows={len(videos_with_notifs)}")


if __name__ == "__main__":
    main()
