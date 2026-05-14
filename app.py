from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai
import os
import json

# ---------- LOAD ENV ----------
load_dotenv()

# ---------- APP ----------
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

# ---------- OPENAI ----------
openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------- STORAGE ----------
STORY_FILE = "data/stories.json"


def ensure_story_file():

    os.makedirs("data", exist_ok=True)

    if not os.path.exists(STORY_FILE):

        with open(STORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def save_story(data):

    ensure_story_file()

    try:

        with open(STORY_FILE, "r", encoding="utf-8") as f:
            stories = json.load(f)

    except:

        stories = []

    stories.append(data)

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)


# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.get_json()

    emojis = data.get("emojis", "")
    theme = data.get("theme", "")

    if not emojis or not theme:

        return jsonify({
            "error": "Theme and emojis are required"
        }), 400

    try:

        # ---------- STORY ----------
        prompt = f"""
Write a short magical story in English.

Theme: {theme}
Emojis: {emojis}

Rules:
- Inspired by One Thousand and One Nights
- Start with "Once upon a time"
- 4 to 6 sentences
- Beautiful ending
"""

        chat = openai.ChatCompletion.create(

            model="gpt-3.5-turbo",

            messages=[
                {
                    "role": "system",
                    "content": "You are a magical storyteller."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.9,
            max_tokens=250
        )

        story = chat["choices"][0]["message"]["content"]

        # ---------- IMAGE ----------
        image_prompt = f"""
Persian miniature painting.
Traditional Iranian art.
Golden details.
Magical atmosphere.

Theme: {theme}
Emojis: {emojis}
"""

        image = openai.Image.create(

            prompt=image_prompt,

            n=1,

            size="512x512"
        )

        image_url = image["data"][0]["url"]

        # ---------- SAVE ----------
        save_story({

            "theme": theme,
            "emojis": emojis,
            "story": story,
            "image_url": image_url

        })

        return jsonify({

            "story": story,
            "image_url": image_url

        })

    except Exception as e:

        print(e)

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/health")
def health():

    return {
        "status": "ok"
    }


# ---------- RUN ----------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

