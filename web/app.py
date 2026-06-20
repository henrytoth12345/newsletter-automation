import base64
import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TOPICS_FILE = "topics.txt"


def gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def get_topics_file():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{TOPICS_FILE}"
    resp = requests.get(url, headers=gh_headers())
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def put_topics_file(content, sha, message="Update topics via web UI"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{TOPICS_FILE}"
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha,
    }
    requests.put(url, headers=gh_headers(), json=payload).raise_for_status()


def parse_topics(content):
    pending, sent = [], []
    for line in content.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("[SENT]"):
            sent.append(s[6:].strip())
        else:
            pending.append(s)
    return pending, sent


@app.route("/")
def index():
    content, _ = get_topics_file()
    pending, sent = parse_topics(content)
    return render_template("index.html", pending=pending, sent=sent)


@app.route("/topics/add", methods=["POST"])
def add_topics():
    raw = request.form.get("topics", "").strip()
    if not raw:
        return redirect("/")
    new_lines = [l.strip() for l in raw.splitlines() if l.strip()]
    content, sha = get_topics_file()

    lines = content.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            insert_at = i + 1
        else:
            break

    lines[insert_at:insert_at] = new_lines
    put_topics_file("\n".join(lines) + "\n", sha)
    return redirect("/")


@app.route("/topics/delete", methods=["POST"])
def delete_topic():
    topic = request.form.get("topic", "").strip()
    content, sha = get_topics_file()
    lines = [l for l in content.splitlines() if l.strip() != topic]
    put_topics_file("\n".join(lines) + "\n", sha)
    return redirect("/")


@app.route("/trigger", methods=["POST"])
def trigger():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/newsletter.yml/dispatches"
    requests.post(url, headers=gh_headers(), json={"ref": "main"}).raise_for_status()
    return redirect("/?triggered=1")


@app.route("/suggest", methods=["POST"])
def suggest():
    content, _ = get_topics_file()
    pending, sent = parse_topics(content)
    existing = (pending + sent)[:40]
    existing_text = "\n".join(f"- {t}" for t in existing)

    prompt = f"""Here are existing newsletter topics about filmmaking and the film industry:

{existing_text}

Suggest 4 new newsletter topic ideas that are different from the ones above but fit the same theme.
Each topic should be a specific, interesting angle — not generic.
Return ONLY a JSON array of 4 strings, no explanation. Example format:
["Topic one", "Topic two", ...]"""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.9,
        },
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()

    start = text.find("[")
    end = text.rfind("]") + 1
    suggestions = json.loads(text[start:end])
    return jsonify(suggestions=suggestions)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
