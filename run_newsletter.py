"""
Newsletter automation pipeline.

Usage:
    python run_newsletter.py --topic "AI in Healthcare"
    python run_newsletter.py --from-queue          # picks next topic from topics.txt
    python run_newsletter.py --from-queue --skip-images  # fast test
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def pick_next_topic(topics_file: str) -> str:
    if not Path(topics_file).exists():
        print(f"ERROR: {topics_file} not found.", file=sys.stderr)
        sys.exit(1)

    lines = Path(topics_file).read_text().splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("[SENT]"):
            lines[i] = f"[SENT] {stripped}"
            Path(topics_file).write_text("\n".join(lines) + "\n")
            print(f"Topic picked from queue: {stripped}")
            return stripped

    print(f"ERROR: No remaining topics in {topics_file}. Add more topics to continue.", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], step: str) -> None:
    print(f"\n{'='*60}")
    print(f"STEP: {step}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"\nERROR: Step '{step}' failed (exit code {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the newsletter automation pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic", help='Newsletter topic, e.g. "AI in Healthcare"')
    group.add_argument("--from-queue", action="store_true", help="Pick next topic from queue file")
    parser.add_argument("--queue", default="topics.txt", help="Topics file to use (default: topics.txt)")
    parser.add_argument("--recipient", help="Override recipient email")
    parser.add_argument("--renderer", default="tools/render_newsletter.py", help="Renderer script to use")
    parser.add_argument("--skip-images", action="store_true", help="Skip infographic generation")
    args = parser.parse_args()

    topic = pick_next_topic(args.queue) if args.from_queue else args.topic
    slug = slugify(topic)

    research_file = f".tmp/research_{slug}.json"
    images_dir = f".tmp/images/{slug}"
    html_file = f".tmp/newsletter_{slug}.html"
    youtube_file = f".tmp/youtube_{slug}.json"

    Path(".tmp/images").mkdir(parents=True, exist_ok=True)

    # Step 1: Research
    run(
        [sys.executable, "tools/research_topic.py", "--topic", topic],
        "Research topic with Groq",
    )

    # Step 2a: Fetch YouTube videos
    run(
        [sys.executable, "tools/fetch_youtube.py", "--topic", topic, "--output", youtube_file],
        "Fetch YouTube videos",
    )

    # Step 2: Generate infographics (one per section)
    if not args.skip_images:
        with open(research_file) as f:
            research = json.load(f)

        for i, section in enumerate(research.get("sections", [])):
            prompt = section.get("infographic_prompt", f"Infographic about {section['title']} related to {topic}")
            output_path = f"{images_dir}/{slug}_{i}.html"
            run(
                [
                    sys.executable,
                    "tools/generate_infographic.py",
                    "--prompt",
                    prompt,
                    "--output",
                    output_path,
                ],
                f"Generate infographic {i+1}/{len(research['sections'])}: {section['title']}",
            )
    else:
        print("\nSkipping infographic generation (--skip-images)")
        images_dir = ""

    # Step 3: Render HTML
    run(
        [
            sys.executable,
            args.renderer,
            "--research", research_file,
            "--images-dir", images_dir or ".tmp/images/none",
            "--youtube", youtube_file,
            "--output", html_file,
        ],
        "Render newsletter HTML",
    )

    # Step 4: Send via Gmail
    with open(research_file) as f:
        research = json.load(f)

    subject = research.get("subject_line", f"Newsletter: {topic}")
    recipient = args.recipient or os.getenv("NEWSLETTER_RECIPIENT", "henrypaultoth@gmail.com")

    run(
        [
            sys.executable,
            "tools/send_gmail.py",
            "--html-file", html_file,
            "--subject", subject,
            "--to", recipient,
        ],
        f"Send email to {recipient}",
    )

    print(f"\n{'='*60}")
    print(f"Newsletter sent to {recipient}")
    print(f"Topic: {topic}")
    print(f"Subject: {subject}")
    print(f"HTML saved at: {html_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
