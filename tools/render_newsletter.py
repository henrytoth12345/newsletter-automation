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

LOGO_URL = "https://raw.githubusercontent.com/henrytoth12345/newsletter-automation/main/assets/logo.png"
ACCENT = "#e8232a"


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


def render_youtube_section(youtube_file: str) -> str:
    path = Path(youtube_file)
    if not path.exists():
        return ""
    try:
        videos = json.loads(path.read_text())
    except Exception:
        return ""
    if not videos:
        return ""

    cards = ""
    for v in videos:
        cards += f'''
        <a href="{v['url']}" target="_blank"
           style="display:block;text-decoration:none;margin-bottom:16px;
                  border:1px solid #e8e8e8;border-radius:6px;overflow:hidden;">
          <div style="position:relative;">
            <img src="{v['thumbnail']}" alt="{v['title']}"
                 style="width:100%;display:block;border-bottom:1px solid #e8e8e8;">
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                        width:52px;height:52px;background:rgba(0,0,0,0.7);border-radius:50%;
                        display:flex;align-items:center;justify-content:center;">
              <div style="width:0;height:0;border-top:10px solid transparent;
                          border-bottom:10px solid transparent;
                          border-left:18px solid white;margin-left:4px;"></div>
            </div>
          </div>
          <div style="padding:12px 14px;background:#fff;">
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                        font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:4px;
                        line-height:1.4;">
              {v['title']}
            </div>
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                        font-size:12px;color:#888;">
              {v['channel']}
            </div>
          </div>
        </a>'''

    return f'''
    <div style="margin-bottom:40px;">
      <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                  font-size:11px;font-weight:800;letter-spacing:0.12em;
                  color:{ACCENT};text-transform:uppercase;margin-bottom:14px;">
        Watch
      </div>
      {cards}
      <div style="border-top:1px solid #e8e8e8;margin-top:8px;"></div>
    </div>'''


def render(research: dict, images_dir: str, youtube_file: str = "") -> str:
    slug = slugify(research["topic"])
    sections = research.get("sections", [])

    # Logo header
    header_html = f'''
    <div style="text-align:center;padding:32px 0 16px;">
      <img src="{LOGO_URL}" alt="Newsletter" style="max-width:220px;height:auto;display:inline-block;">
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
              <strong style="color:#1a1a1a;">{s.get("title", "")}:</strong>
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
            {section.get("title", "")}
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
      {render_youtube_section(youtube_file)}
      {footer_html}
    </div>
  </div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Render newsletter HTML")
    parser.add_argument("--research", required=True, help="Path to research JSON file")
    parser.add_argument("--images-dir", required=True, help="Directory containing infographic HTML files")
    parser.add_argument("--youtube", default="", help="Path to YouTube JSON file")
    parser.add_argument("--output", help="Output HTML file path (auto-derived if omitted)")
    args = parser.parse_args()

    if not Path(args.research).exists():
        print(f"ERROR: Research file not found: {args.research}", file=sys.stderr)
        sys.exit(1)

    with open(args.research) as f:
        research = json.load(f)

    html = render(research, args.images_dir, args.youtube)

    output_path = args.output or f".tmp/newsletter_{slugify(research['topic'])}.html"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Newsletter rendered to {output_path}")


if __name__ == "__main__":
    main()
