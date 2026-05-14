from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

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


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "OPENAI_API_KEY is missing"}), 500

        client = OpenAI(api_key=api_key)

        data = request.get_json(silent=True) or request.form.to_dict()

        emojis = (data.get("emojis") or "").strip()
        theme = (data.get("theme") or "").strip()

        if not emojis or not theme:
            return jsonify({"error": "Emojis and theme are required"}), 400

        story_prompt = (
            "Write a short, self-contained English story, about 4–6 sentences. "
            "Style: a modern, global echo of One Thousand and One Nights where any person can be the storyteller. "
            "Do NOT mention Scheherazade or a king. "
            "Begin the first sentence with 'Once' or 'Once upon a time'. "
            "End with a satisfying, closed resolution. "
            "Keep language vivid but simple. "
            f"Inspiration emojis: {emojis}. Theme: {theme}."
        )

        story_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise, imaginative writer. "
                        "Your stories always begin with Once or Once upon a time "
                        "and end with a clear, satisfying ending."
                    ),
                },
                {
                    "role": "user",
                    "content": story_prompt,
                },
            ],
            temperature=0.9,
            max_tokens=400,
        )

        story = story_response.choices[0].message.content.strip()

        if story and not story.lower().startswith(("once ", "once upon a time")):
            story = "Once, " + story

        if story and story[-1] not in ".!?":
            story += "."

        image_prompt = (
            "Create a beautiful illustration in the style of Persian miniature "
            "and traditional Iranian painting: delicate lines, ornamental patterns, "
            "gold accents, harmonious colors, poetic atmosphere, magical composition. "
            f"Reflect these emojis and theme. Emojis: {emojis}; Theme: {theme}."
        )

        image_response = client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            size="1024x1024",
            n=1,
        )

        image_base64 = image_response.data[0].b64_json
        image_url = "data:image/png;base64," + image_base64

        result = {
            "story": story,
            "image_url": image_url,
        }

        save_story({
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url,
        })

        return jsonify(result)

    except Exception as e:
        print("ERROR /generate:", repr(e))
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
