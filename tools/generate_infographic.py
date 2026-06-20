"""
Generates an HTML infographic block using Groq.

Produces a self-contained HTML snippet (inline styles only, no external resources)
that embeds directly into the newsletter and renders in Gmail and browsers.

Usage:
    python tools/generate_infographic.py --prompt "..." --output ".tmp/images/slug/slug_0.html"
"""

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are a data visualization designer. Given a description of an infographic concept,
produce a self-contained HTML block that looks like a polished infographic.

Rules:
- Output ONLY the HTML block (a single <div>), no <!DOCTYPE>, no <html>, no <head>, no <body>
- Use ONLY inline styles (no <style> tags, no CSS classes, no external resources)
- Max width: 560px. Use a clean, modern design with a dark header and light content area.
- Include relevant icons using Unicode characters (✓ ● ▶ → ★ etc.)
- Make it visually rich: use colored boxes, stat callouts, numbered lists, comparison layouts
- All text must be readable: good contrast, 13-15px body text
- No JavaScript. No images. No external fonts.
- The infographic should illustrate the concept described, using realistic-looking data and labels"""


def generate_infographic(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Create an infographic for: {prompt}"},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    return raw


def main():
    parser = argparse.ArgumentParser(description="Generate an HTML infographic using Groq")
    parser.add_argument("--prompt", required=True, help="Description of the infographic to generate")
    parser.add_argument("--output", required=True, help="Output file path (.html)")
    args = parser.parse_args()

    print(f"Generating infographic: {args.prompt[:80]}...")
    html_block = generate_infographic(args.prompt)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        f.write(html_block)

    print(f"Infographic saved to {args.output}")


if __name__ == "__main__":
    main()
