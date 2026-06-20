"""
Renders the newsletter as a self-contained HTML file.
Embeds Claude-generated HTML infographic blocks inline per section.

Usage:
    python tools/render_newsletter.py --research .tmp/research_slug.json --images-dir .tmp/images/slug/

Output:
    .tmp/newsletter_{slug}.html
"""

import argparse
import json
import re
import sys
from pathlib import Path


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject_line}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: #f4f4f5;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      color: #1a1a2e;
      padding: 24px 16px;
    }}
    .wrapper {{
      max-width: 620px;
      margin: 0 auto;
    }}
    .header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      border-radius: 12px 12px 0 0;
      padding: 36px 40px;
      text-align: center;
    }}
    .header-label {{
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.15em;
      color: #a0a0c0;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .header h1 {{
      font-size: 26px;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.3;
    }}
    .preview-text {{
      font-size: 14px;
      color: #8888aa;
      margin-top: 10px;
    }}
    .content {{
      background: #ffffff;
    }}
    .section {{
      padding: 36px 40px;
      border-bottom: 1px solid #f0f0f5;
    }}
    .section:last-child {{
      border-bottom: none;
    }}
    .section-number {{
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #6c63ff;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .section h2 {{
      font-size: 20px;
      font-weight: 700;
      color: #1a1a2e;
      margin-bottom: 16px;
      line-height: 1.3;
    }}
    .section p {{
      font-size: 15px;
      line-height: 1.75;
      color: #3d3d5c;
      margin-bottom: 14px;
    }}
    .section p:last-of-type {{
      margin-bottom: 0;
    }}
    .infographic-wrap {{
      margin-top: 24px;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid #eeeef5;
    }}
    .footer {{
      background: #f9f9fc;
      border-radius: 0 0 12px 12px;
      padding: 28px 40px;
      text-align: center;
      border-top: 1px solid #eeeef5;
    }}
    .footer p {{
      font-size: 12px;
      color: #9999b0;
      line-height: 1.6;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="header-label">Newsletter</div>
      <h1>{subject_line}</h1>
      <div class="preview-text">{preview_text}</div>
    </div>
    <div class="content">
      {sections_html}
    </div>
    <div class="footer">
      <p>You're receiving this because you subscribed to this newsletter.<br>
      Researched and written with Claude AI.</p>
    </div>
  </div>
</body>
</html>
"""


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def find_section_infographic(images_dir: str, section_index: int, slug: str) -> str | None:
    images_path = Path(images_dir)
    if not images_path.exists():
        return None

    candidates = [
        images_path / f"{slug}_{section_index}.html",
        images_path / f"section_{section_index}.html",
        images_path / f"{section_index}.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text()

    # Fallback: sort all .html files and pick by index
    html_files = sorted(images_path.glob("*.html"))
    if section_index < len(html_files):
        return html_files[section_index].read_text()

    return None


def body_to_paragraphs(body: str) -> str:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [body.strip()]
    return "\n      ".join(f"<p>{p}</p>" for p in paragraphs)


def render(research: dict, images_dir: str) -> str:
    slug = slugify(research["topic"])
    ordinals = ["01", "02", "03", "04", "05"]
    sections_html_parts = []

    for i, section in enumerate(research.get("sections", [])):
        infographic_html = find_section_infographic(images_dir, i, slug)
        infographic_block = (
            f'<div class="infographic-wrap">{infographic_html}</div>'
            if infographic_html
            else ""
        )

        section_html = f"""\
<div class="section">
  <div class="section-number">{ordinals[i] if i < len(ordinals) else f"{i+1:02d}"}</div>
  <h2>{section["title"]}</h2>
  {body_to_paragraphs(section.get("body", ""))}
  {infographic_block}
</div>"""
        sections_html_parts.append(section_html)

    return HTML_TEMPLATE.format(
        subject_line=research.get("subject_line", research["topic"]),
        preview_text=research.get("preview_text", ""),
        sections_html="\n      ".join(sections_html_parts),
    )


def main():
    parser = argparse.ArgumentParser(description="Render newsletter HTML from research JSON")
    parser.add_argument("--research", required=True, help="Path to research JSON file")
    parser.add_argument("--images-dir", required=True, help="Directory containing section infographic HTML files")
    parser.add_argument("--output", help="Output HTML file path (auto-derived if omitted)")
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

    print(f"Newsletter rendered to {output_path}")


if __name__ == "__main__":
    main()
