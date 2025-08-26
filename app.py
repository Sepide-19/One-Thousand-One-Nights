from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import json
import openai

# Load envs (for local runs)
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# OpenAI key (SDK 0.28.x style)
openai.api_key = os.getenv("OPENAI_API_KEY")

STORY_FILE = "data/stories.json"


# ---------- storage helpers ----------
def ensure_story_file():
    os.makedirs(os.path.dirname(STORY_FILE), exist_ok=True)
    if not os.path.exists(STORY_FILE):
        with open(STORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def save_story(entry: dict):
    ensure_story_file()
    try:
        with open(STORY_FILE, "r", encoding="utf-8") as f:
            stories = json.load(f)
            if not isinstance(stories, list):
                stories = []
    except Exception:
        stories = []
    stories.append(entry)
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)


# ---------- routes ----------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    # accept JSON or form
    data = request.get_json(silent=True) or request.form.to_dict()
    emojis = (data.get("emojis") or "").strip()
    theme = (data.get("theme") or "").strip()

    if not emojis or not theme:
        return jsonify({"error": "Emojis and theme are required"}), 400

    try:
        # ---- story: modern-global 1001 Nights, clear start & closed ending (~4–6 sentences) ----
        story_prompt = (
            "Write a short, self-contained English story (about 4–6 sentences). "
            "Style: a modern, global echo of One Thousand and One Nights where any person can be the storyteller. "
            "Do NOT mention Scheherazade or a king. "
            "Begin the first sentence with 'Once' or 'Once upon a time'. "
            "End with a satisfying, closed resolution (no cliffhanger, no 'to be continued'). "
            "Keep language vivid but simple; contemporary tone with a touch of wonder. "
            f"Inspiration emojis: {emojis}. Theme: {theme}."
        )

        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise, imaginative writer. "
                        "Your stories always begin with 'Once' (or 'Once upon a time') "
                        "and conclude with a clear, satisfying ending—no open hooks."
                    )
                },
                {"role": "user", "content": story_prompt}
            ],
            temperature=0.9,
            max_tokens=400
        )
        story = chat["choices"][0]["message"]["content"].strip()

        # Soft guardrails: ensure opening with 'Once' and a terminal punctuation.
        if story and not story.lower().startswith(("once ", "once upon a time")):
            story = "Once, " + story[0].lower() + story[1:]
        if story and story[-1] not in ".!?":
            story += "."

        # ---- image (Persian miniature style) ----
        image_prompt = (
            "Create a beautiful illustration in the style of Persian miniature "
            "(Iranian traditional art): delicate lines, ornamental patterns, gold accents, "
            f"harmonious palette. Reflect these emojis and theme. Emojis: {emojis}; Theme: {theme}."
        )
        image = openai.Image.create(
            prompt=image_prompt,
            n=1,
            size="512x512"
        )
        image_url = image["data"][0]["url"]

        result = {"story": story, "image_url": image_url}

        # persist
        save_story({
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url
        })

        return jsonify(result)

    except Exception as e:
        print("❌ /generate error:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
