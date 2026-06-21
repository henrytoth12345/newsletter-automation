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


def gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def get_file(filename):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    resp = requests.get(url, headers=gh_headers())
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def put_file(filename, content, sha, message="Update topics via web UI"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
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


def insert_topics(content, new_lines):
    lines = content.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            insert_at = i + 1
        else:
            break
    lines[insert_at:insert_at] = new_lines
    return "\n".join(lines) + "\n"


def groq_suggest(existing, theme):
    existing_text = "\n".join(f"- {t}" for t in existing[:40])
    prompt = f"""Here are existing newsletter topics about {theme}:

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
    return json.loads(text[start:end])


# ── Filmmaking newsletter ──────────────────────────────────────────────

@app.route("/")
def index():
    content, _ = get_file("topics.txt")
    pending, sent = parse_topics(content)
    return render_template("index.html", pending=pending, sent=sent)


@app.route("/topics/add", methods=["POST"])
def add_topics():
    raw = request.form.get("topics", "").strip()
    if not raw:
        return redirect("/")
    new_lines = [l.strip() for l in raw.splitlines() if l.strip()]
    content, sha = get_file("topics.txt")
    put_file("topics.txt", insert_topics(content, new_lines), sha)
    return redirect("/")


@app.route("/topics/delete", methods=["POST"])
def delete_topic():
    topic = request.form.get("topic", "").strip()
    content, sha = get_file("topics.txt")
    lines = [l for l in content.splitlines() if l.strip() != topic]
    put_file("topics.txt", "\n".join(lines) + "\n", sha)
    return redirect("/")


@app.route("/trigger", methods=["POST"])
def trigger():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/newsletter.yml/dispatches"
    requests.post(url, headers=gh_headers(), json={"ref": "main"}).raise_for_status()
    return redirect("/")


@app.route("/suggest", methods=["POST"])
def suggest():
    content, _ = get_file("topics.txt")
    pending, sent = parse_topics(content)
    suggestions = groq_suggest(pending + sent, "filmmaking and the film industry")
    return jsonify(suggestions=suggestions)


# ── Learn newsletter ──────────────────────────────────────────────────

@app.route("/learn")
def learn_index():
    content, _ = get_file("topics_learn.txt")
    pending, sent = parse_topics(content)
    return render_template("learn.html", pending=pending, sent=sent)


@app.route("/learn/topics/add", methods=["POST"])
def learn_add_topics():
    raw = request.form.get("topics", "").strip()
    if not raw:
        return redirect("/learn")
    new_lines = [l.strip() for l in raw.splitlines() if l.strip()]
    content, sha = get_file("topics_learn.txt")
    put_file("topics_learn.txt", insert_topics(content, new_lines), sha)
    return redirect("/learn")


@app.route("/learn/topics/delete", methods=["POST"])
def learn_delete_topic():
    topic = request.form.get("topic", "").strip()
    content, sha = get_file("topics_learn.txt")
    lines = [l for l in content.splitlines() if l.strip() != topic]
    put_file("topics_learn.txt", "\n".join(lines) + "\n", sha)
    return redirect("/learn")


@app.route("/learn/trigger", methods=["POST"])
def learn_trigger():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/newsletter_learn.yml/dispatches"
    requests.post(url, headers=gh_headers(), json={"ref": "main"}).raise_for_status()
    return redirect("/learn")


@app.route("/learn/suggest", methods=["POST"])
def learn_suggest():
    content, _ = get_file("topics_learn.txt")
    pending, sent = parse_topics(content)
    suggestions = groq_suggest(pending + sent, "filmmaking skills — color grading, editing, storytelling, cinematography, and business")
    return jsonify(suggestions=suggestions)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
