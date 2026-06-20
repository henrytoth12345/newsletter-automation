"""
Renders the newsletter as a self-contained HTML file styled like The Hustle.

Usage:
    python tools/render_newsletter.py --research .tmp/research_slug.json --images-dir .tmp/images/slug/

Output:
    .tmp/newsletter_{slug}.html
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path

LOGO_PATH = Path(__file__).parent.parent / "assets" / "logo.png"
ACCENT = "#e8232a"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def get_logo_data_uri() -> str | None:
    if LOGO_PATH.exists():
        data = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f"data:image/png;base64,{data}"
    return None


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
    html_files = sorted(images_path.glob("*.html"))
    if section_index < len(html_files):
        return html_files[section_index].read_text()
    return None


def body_to_paragraphs(body: str) -> str:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [body.strip()]
    return "".join(
        f'<p style="margin:0 0 16px 0;font-size:16px;line-height:1.7;color:#1a1a1a;">{p}</p>'
        for p in paragraphs
    )


def render(research: dict, images_dir: str) -> str:
    slug = slugify(research["topic"])
    logo_uri = get_logo_data_uri()
    sections = research.get("sections", [])

    # Logo header
    if logo_uri:
        header_html = f'''
        <div style="text-align:center;padding:32px 0 16px;">
          <img src="{logo_uri}" alt="Newsletter" style="max-width:220px;height:auto;display:inline-block;">
        </div>'''
    else:
        header_html = f'''
        <div style="text-align:center;padding:32px 0 16px;">
          <div style="font-family:Georgia,serif;font-size:36px;font-weight:900;color:#1a1a1a;letter-spacing:-1px;">
            {research.get("topic", "Newsletter")}
          </div>
        </div>'''

    # Divider
    divider = f'<div style="border-top:3px solid {ACCENT};margin:0 0 24px 0;"></div>'

    # Preview / intro blurb
    preview = research.get("preview_text", "")
    preview_html = f'''
    <p style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
              font-size:17px;line-height:1.6;color:#1a1a1a;margin:0 0 24px 0;">
      {preview}
    </p>''' if preview else ""

    # Today's rundown bullets
    rundown_items = "".join(
        f'''<li style="margin-bottom:6px;">
              <strong style="color:#1a1a1a;">{s["title"]}:</strong>
              <span style="color:#444;"> {s.get("body","")[:100].split(".")[0]}.</span>
            </li>'''
        for s in sections
    )
    rundown_html = f'''
    <div style="margin:0 0 28px 0;">
      <p style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                font-size:15px;font-weight:700;color:#1a1a1a;margin:0 0 10px 0;">
        Today's rundown:
      </p>
      <ul style="margin:0;padding-left:20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 font-size:15px;line-height:1.6;color:#1a1a1a;">
        {rundown_items}
      </ul>
    </div>
    <p style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
              font-size:16px;color:#1a1a1a;margin:0 0 32px 0;">Let's do it.</p>'''

    # Sections
    sections_html = ""
    for i, section in enumerate(sections):
        infographic_html = find_section_infographic(images_dir, i, slug)
        infographic_block = (
            f'<div style="margin:20px 0 24px 0;border-radius:8px;overflow:hidden;">{infographic_html}</div>'
            if infographic_html else ""
        )

        sections_html += f'''
        <div style="margin-bottom:40px;">
          <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                      font-size:11px;font-weight:800;letter-spacing:0.12em;
                      color:{ACCENT};text-transform:uppercase;margin-bottom:10px;">
            {section["title"]}
          </div>
          <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
            {body_to_paragraphs(section.get("body", ""))}
          </div>
          {infographic_block}
          <div style="border-top:1px solid #e8e8e8;margin-top:8px;"></div>
        </div>'''

    # Footer
    footer_html = f'''
    <div style="text-align:center;padding:24px 0 8px;
                font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                font-size:12px;color:#999;line-height:1.6;">
      You're receiving this newsletter because you signed up.<br>
      Written with AI assistance.
    </div>'''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{research.get("subject_line", research["topic"])}</title>
</head>
<body style="margin:0;padding:0;background:#f0f0f0;">
  <div style="max-width:600px;margin:32px auto;background:#ffffff;
              border-radius:4px;overflow:hidden;
              box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <div style="padding:0 40px 40px;">
      {header_html}
      {divider}
      {preview_html}
      {rundown_html}
      {sections_html}
      {footer_html}
    </div>
  </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Render newsletter HTML")
    parser.add_argument("--research", required=True, help="Path to research JSON file")
    parser.add_argument("--images-dir", required=True, help="Directory containing infographic HTML files")
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
