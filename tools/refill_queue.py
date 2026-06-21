"""
Refills a topic queue file using Groq when it runs low.

Usage:
    python tools/refill_queue.py --queue topics.txt --theme "filmmaking" --threshold 10 --refill 20
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


def parse_topics(content):
    pending, sent, all_topics = [], [], []
    for line in content.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[SENT]"):
            topic = s[6:].strip()
            sent.append(topic)
            all_topics.append(topic)
        else:
            pending.append(s)
            all_topics.append(s)
    return pending, sent, all_topics


def generate_topics(existing: list[str], theme: str, count: int) -> list[str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    existing_text = "\n".join(f"- {t}" for t in existing[-60:])
    prompt = f"""Here are existing newsletter topics about {theme}:

{existing_text}

Generate {count} brand new newsletter topic ideas that:
- Are completely different from the ones listed above
- Are specific and interesting, not generic
- Fit the same theme of {theme}

Return ONLY a JSON array of {count} strings, no explanation.
Example: ["Topic one", "Topic two", ...]"""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0,
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    start = text.find("[")
    end = text.rfind("]") + 1
    return json.loads(text[start:end])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True, help="Path to topics file")
    parser.add_argument("--theme", required=True, help="Theme description for Groq")
    parser.add_argument("--threshold", type=int, default=10, help="Refill when pending drops below this")
    parser.add_argument("--refill", type=int, default=20, help="Number of topics to generate")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    if not queue_path.exists():
        print(f"ERROR: {args.queue} not found", file=sys.stderr)
        sys.exit(1)

    content = queue_path.read_text()
    pending, sent, all_topics = parse_topics(content)

    print(f"Queue: {len(pending)} pending, {len(sent)} sent")

    if len(pending) >= args.threshold:
        print(f"Queue is healthy ({len(pending)} >= {args.threshold}), no refill needed.")
        return

    print(f"Queue low — generating {args.refill} new topics...")
    new_topics = generate_topics(all_topics, args.theme, args.refill)

    # Append new topics at the bottom of the file
    additions = "\n# --- AUTO-GENERATED ---\n" + "\n".join(new_topics) + "\n"
    queue_path.write_text(content.rstrip() + "\n" + additions)

    print(f"Added {len(new_topics)} new topics to {args.queue}")
    for t in new_topics:
        print(f"  + {t}")


if __name__ == "__main__":
    main()
