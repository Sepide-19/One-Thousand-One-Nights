from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import json
import openai

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

STORY_FILE = "data/stories.json"


# ---------- storage helpers ----------
def ensure_story_file():
    os.makedirs(os.path.dirname(STORY_FILE), exist_ok=True)

    if not os.path.exists(STORY_FILE):
        with open(STORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def save_story(entry):
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
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    # receive form/json
    data = request.get_json(silent=True) or request.form.to_dict()

    emojis = (data.get("emojis") or "").strip()
    theme = (data.get("theme") or "").strip()

    if not emojis or not theme:
        return jsonify({"error": "Emojis and theme are required"}), 400

    try:

        # ---------- STORY ----------
        story_prompt = (
            "Write a short magical story in English (4-6 sentences). "
            "Inspired by One Thousand and One Nights. "
            "Begin with 'Once' or 'Once upon a time'. "
            "End with a complete satisfying ending. "
            f"Theme: {theme}. Emojis: {emojis}."
        )

        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a poetic storyteller."
                },
                {
                    "role": "user",
                    "content": story_prompt
                }
            ],
            temperature=0.9,
            max_tokens=300
        )

        story = chat["choices"][0]["message"]["content"].strip()

        # ---------- IMAGE ----------
        image_prompt = (
            "Persian miniature painting, delicate details, "
            "traditional Iranian miniature art, gold accents, "
            "ornamental composition, poetic atmosphere. "
            f"Theme: {theme}. Emojis: {emojis}."
        )

        image = openai.Image.create(
            model="gpt-image-1",
            prompt=image_prompt,
            n=1,
            size="1024x1024"
        )

        image_url = (
            "data:image/png;base64," +
            image["data"][0]["b64_json"]
        )

        # ---------- RESULT ----------
        result = {
            "story": story,
            "image_url": image_url
        }

        # save story
        save_story({
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url
        })

        return jsonify(result)

    except Exception as e:
        print("ERROR:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

