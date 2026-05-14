from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STORY_FILE = "data/stories.json"


def ensure_story_file():
    os.makedirs("data", exist_ok=True)
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or request.form.to_dict()

    emojis = (data.get("emojis") or "").strip()
    theme = (data.get("theme") or "").strip()

    if not emojis or not theme:
        return jsonify({"error": "Emojis and theme are required"}), 400

    try:
        story_prompt = (
            "Write a short magical story in English, 4 to 6 sentences. "
            "Inspired by One Thousand and One Nights, but modern and global. "
            "Begin with 'Once upon a time'. "
            "End with a complete satisfying ending. "
            f"Theme: {theme}. Emojis: {emojis}."
        )

        story_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a poetic, concise storyteller."
                },
                {
                    "role": "user",
                    "content": story_prompt
                }
            ],
            temperature=0.9,
            max_tokens=350
        )

        story = story_response.choices[0].message.content.strip()

        image_prompt = (
            "Create a Persian miniature style illustration: traditional Iranian art, "
            "delicate lines, ornamental patterns, gold accents, poetic atmosphere, "
            "magical and beautiful. "
            f"Theme: {theme}. Emojis: {emojis}."
        )

        image_response = client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            size="1024x1024",
            n=1
        )

        image_base64 = image_response.data[0].b64_json
        image_url = "data:image/png;base64," + image_base64

        result = {
            "story": story,
            "image_url": image_url
        }

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
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
