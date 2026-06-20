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

TOPICS_FILE = "topics.txt"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def pick_next_topic() -> str:
    if not Path(TOPICS_FILE).exists():
        print(f"ERROR: {TOPICS_FILE} not found.", file=sys.stderr)
        sys.exit(1)

    lines = Path(TOPICS_FILE).read_text().splitlines()

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("[SENT]"):
            # Mark as sent
            lines[i] = f"[SENT] {stripped}"
            Path(TOPICS_FILE).write_text("\n".join(lines) + "\n")
            print(f"Topic picked from queue: {stripped}")
            return stripped

    print("ERROR: No remaining topics in topics.txt. Add more topics to continue.", file=sys.stderr)
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
    group.add_argument("--from-queue", action="store_true", help=f"Pick next topic from {TOPICS_FILE}")
    parser.add_argument("--skip-images", action="store_true", help="Skip infographic generation (useful for testing)")
    args = parser.parse_args()

    topic = pick_next_topic() if args.from_queue else args.topic
    slug = slugify(topic)

    research_file = f".tmp/research_{slug}.json"
    images_dir = f".tmp/images/{slug}"
    html_file = f".tmp/newsletter_{slug}.html"

    Path(".tmp/images").mkdir(parents=True, exist_ok=True)

    # Step 1: Research
    run(
        [sys.executable, "tools/research_topic.py", "--topic", topic],
        "Research topic with Groq",
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
            "tools/render_newsletter.py",
            "--research", research_file,
            "--images-dir", images_dir or ".tmp/images/none",
            "--output", html_file,
        ],
        "Render newsletter HTML",
    )

    # Step 4: Send via Gmail
    with open(research_file) as f:
        research = json.load(f)

    subject = research.get("subject_line", f"Newsletter: {topic}")
    recipient = os.getenv("NEWSLETTER_RECIPIENT", "henrypaultoth@gmail.com")

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
