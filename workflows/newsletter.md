# Workflow: Newsletter Automation

## Objective
Generate and send a polished, multi-section HTML newsletter on any topic. Claude handles both research and infographic generation. Gmail API delivers the email.

## Required Inputs
- `topic` — the newsletter subject (e.g. "AI in Healthcare", "Future of Solar Energy")

## Required Setup (one-time)
1. Fill in `.env`:
   - `ANTHROPIC_API_KEY` — from console.anthropic.com → API Keys
   - `NEWSLETTER_RECIPIENT` — recipient email (default: henrypaultoth@gmail.com)
2. Download `credentials.json` from Google Cloud Console:
   - Enable Gmail API → Create OAuth 2.0 Client ID (Desktop app) → Download JSON
   - Place in project root as `credentials.json`
3. Run first-time Gmail auth: `python tools/send_gmail.py --setup`
4. Install dependencies: `pip install -r requirements.txt`

## Pipeline (4 Steps)

### Step 1 — Research
```
python tools/research_topic.py --topic "<topic>"
```
- Calls `claude-sonnet-4-6` with a structured JSON prompt
- Outputs: `.tmp/research_{slug}.json`
- JSON contains: `topic`, `subject_line`, `preview_text`, `sections[{title, body, infographic_prompt}]`
- 5 sections: Overview, Key Findings, Data & Statistics, Expert Perspectives, Takeaways & Action Items

### Step 2 — Generate Infographics
```
python tools/generate_infographic.py --prompt "<prompt>" --output ".tmp/images/{slug}/{slug}_{i}.html"
```
Run once per section (5 total). Each section's `infographic_prompt` from Step 1 is used.
- Claude generates a self-contained HTML block (inline styles only, no external resources)
- Output is an HTML snippet, not an image — embeds directly in the newsletter HTML
- This is Gmail-compatible: no image hosting or base64 encoding required

### Step 3 — Render HTML
```
python tools/render_newsletter.py --research .tmp/research_{slug}.json --images-dir .tmp/images/{slug}/
```
- Embeds each infographic HTML block inline into the newsletter
- Outputs: `.tmp/newsletter_{slug}.html` (preview this in a browser before sending)

### Step 4 — Send via Gmail
```
python tools/send_gmail.py --html-file .tmp/newsletter_{slug}.html --subject "<subject>" --to henrypaultoth@gmail.com
```
- Uses Gmail API with OAuth2 (`token.json` auto-refreshes after first setup)

## Shortcut: Run Everything
```
python run_newsletter.py --topic "AI in Healthcare"
```
Runs all 4 steps in sequence. Use `--skip-images` to skip infographic generation during testing.

## Edge Cases & Known Behavior

### Claude (Research + Infographics)
- Both tools use `claude-sonnet-4-6`. Downgrade to `claude-haiku-4-5-20251001` for lower cost if needed.
- Research output must be valid JSON. If Claude wraps it in markdown fences, the tool strips them automatically.
- Infographics are HTML blocks with inline styles — they render in browsers and Gmail web. Some email apps may handle them differently; preview in browser first.

### Gmail
- `token.json` stores the refresh token. If it expires or is revoked, rerun `python tools/send_gmail.py --setup`.
- Gmail API scope: `gmail.send` (send-only, does not read inbox).

## Output Files
| File | Description |
|------|-------------|
| `.tmp/research_{slug}.json` | Structured research data |
| `.tmp/images/{slug}/{slug}_{i}.html` | Claude-generated HTML infographic blocks |
| `.tmp/newsletter_{slug}.html` | Final rendered newsletter (open in browser to preview) |

All `.tmp/` files are disposable and regenerated on each run.

## Improvement Log
_(Update this section when you discover new constraints, errors, or better approaches)_

- **[date]** — Notes go here
