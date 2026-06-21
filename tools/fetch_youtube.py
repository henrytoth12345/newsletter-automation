"""
Fetches relevant YouTube videos for a newsletter topic.

Usage:
    python tools/fetch_youtube.py --topic "Color Grading" --output .tmp/youtube_slug.json

Output:
    JSON array of {title, channel, url, thumbnail}
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def fetch_videos(topic: str, max_results: int = 2) -> list[dict]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("ERROR: YOUTUBE_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    resp = requests.get(YOUTUBE_SEARCH_URL, params={
        "part": "snippet",
        "q": topic,
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": "en",
        "key": api_key,
    }, timeout=10)
    resp.raise_for_status()

    videos = []
    for item in resp.json().get("items", []):
        vid_id = item["id"]["videoId"]
        snippet = item["snippet"]
        videos.append({
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={vid_id}",
            "thumbnail": snippet["thumbnails"]["high"]["url"],
        })
    return videos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    videos = fetch_videos(args.topic)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(videos, f, indent=2)

    print(f"Fetched {len(videos)} videos → {args.output}")


if __name__ == "__main__":
    main()
