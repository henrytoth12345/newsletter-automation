"""
Renders the "One Thing to Learn" newsletter — a single focused daily lesson.

Usage:
    python tools/render_learn.py --research .tmp/research_slug.json --images-dir .tmp/images/slug/

Output:
    .tmp/newsletter_{slug}.html
"""

import argparse
import json
import re
import sys
from pathlib import Path

LOGO_URL = "https://raw.githubusercontent.com/henrytoth12345/newsletter-automation/main/assets/logo.png"
ACCENT = "#e8232a"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def body_to_paragraphs(body: str) -> str:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [body.strip()]
    return "".join(
        f'<p style="margin:0 0 16px 0;font-size:16px;line-height:1.8;color:#1a1a1a;">{p}</p>'
        for p in paragraphs
    )


def render(research: dict, images_dir: str) -> str:
    topic = research.get("topic", "Today's Lesson")
    sections = research.get("sections", [])

    header_html = f'''
    <div style="text-align:center;padding:32px 0 8px;">
      <img src="{LOGO_URL}" alt="Newsletter" style="max-width:180px;height:auto;display:inline-block;">
    </div>
    <div style="text-align:center;padding:8px 0 24px;">
      <span style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                   font-size:11px;font-weight:800;letter-spacing:0.14em;
                   color:{ACCENT};text-transform:uppercase;">
        One Thing to Learn Today
      </span>
    </div>'''

    divider = f'<div style="border-top:3px solid {ACCENT};margin:0 0 28px 0;"></div>'

    topic_html = f'''
    <h1 style="font-family:Georgia,serif;font-size:28px;font-weight:900;
               color:#1a1a1a;margin:0 0 24px 0;line-height:1.25;
               letter-spacing:-0.02em;">
      {topic}
    </h1>'''

    sections_html = ""
    for section in sections:
        sections_html += f'''
        <div style="margin-bottom:32px;">
          <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                      font-size:10px;font-weight:800;letter-spacing:0.14em;
                      color:{ACCENT};text-transform:uppercase;margin-bottom:10px;">
            {section["title"]}
          </div>
          <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
            {body_to_paragraphs(section.get("body", ""))}
          </div>
          <div style="border-top:1px solid #e8e8e8;margin-top:4px;"></div>
        </div>'''

    footer_html = f'''
    <div style="text-align:center;padding:24px 0 8px;
                font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                font-size:12px;color:#999;line-height:1.6;">
      One thing, every day.<br>
      Written with AI assistance.
    </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{topic}</title>
</head>
<body style="margin:0;padding:0;background:#f0f0f0;">
  <div style="max-width:600px;margin:32px auto;background:#ffffff;
              border-radius:4px;overflow:hidden;
              box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <div style="padding:0 40px 40px;">
      {header_html}
      {divider}
      {topic_html}
      {sections_html}
      {footer_html}
    </div>
  </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Render learn newsletter HTML")
    parser.add_argument("--research", required=True)
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--output", help="Output path (auto-derived if omitted)")
    args = parser.parse_args()

    if not Path(args.research).exists():
        print(f"ERROR: Research file not found: {args.research}", file=sys.stderr)
        sys.exit(1)

    with open(args.research) as f:
        research = json.load(f)

    html = render(research, args.images_dir)

    output_path = args.output or f".tmp/newsletter_{slugify(research['topic'])}.html"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Learn newsletter rendered to {output_path}")


if __name__ == "__main__":
    main()
