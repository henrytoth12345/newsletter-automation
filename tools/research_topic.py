"""
Researches a topic using Groq and outputs structured JSON for the newsletter pipeline.

Usage:
    python tools/research_topic.py --topic "AI in Healthcare"

Output:
    .tmp/research_{slug}.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


SYSTEM_PROMPT = """You are a newsletter research assistant. Given a topic, produce a comprehensive,
well-structured research brief formatted as JSON. Be factual, specific, and include real data where possible.

Your output must be valid JSON with exactly this structure:
{
  "topic": "<the topic>",
  "subject_line": "<compelling email subject line, under 60 chars>",
  "preview_text": "<one-sentence email preview, under 100 chars>",
  "sections": [
    {
      "title": "Overview",
      "body": "<3-4 paragraph introduction to the topic>",
      "infographic_prompt": "<describe what data/concept this section's infographic should visualize>"
    },
    {
      "title": "Key Findings",
      "body": "<3-4 paragraphs covering the most important recent developments>",
      "infographic_prompt": "<describe what data/concept this section's infographic should visualize>"
    },
    {
      "title": "Data & Statistics",
      "body": "<3-4 paragraphs with specific numbers, percentages, growth rates, market data>",
      "infographic_prompt": "<describe a data visualization: what numbers to show, what comparisons to make>"
    },
    {
      "title": "Expert Perspectives",
      "body": "<3-4 paragraphs covering what experts, researchers, or industry leaders are saying>",
      "infographic_prompt": "<describe what this section's infographic should visualize>"
    },
    {
      "title": "Takeaways & Action Items",
      "body": "<3-4 paragraphs with practical implications and what readers should do or watch for>",
      "infographic_prompt": "<describe a visual summary: key points, checklist, or action framework>"
    }
  ]
}

Output ONLY the JSON object, no markdown fences, no preamble."""


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:50]


def research_topic(topic: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    client = Groq(api_key=api_key)

    print(f"Researching: {topic}")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Research this topic for a newsletter: {topic}"},
        ],
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse response as JSON: {e}", file=sys.stderr)
        print(f"Raw response:\n{raw}", file=sys.stderr)
        sys.exit(1)

    return data


def main():
    parser = argparse.ArgumentParser(description="Research a topic using Groq")
    parser.add_argument("--topic", required=True, help="The newsletter topic to research")
    args = parser.parse_args()

    Path(".tmp").mkdir(exist_ok=True)

    data = research_topic(args.topic)

    slug = slugify(args.topic)
    output_path = f".tmp/research_{slug}.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Research saved to {output_path}")
    print(f"Subject line: {data.get('subject_line', '')}")
    print(f"Sections: {len(data.get('sections', []))}")


if __name__ == "__main__":
    main()
