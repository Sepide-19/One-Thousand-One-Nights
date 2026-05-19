from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STORY_FILE = "data/stories.json"


def ensure_data_folder():
    if not os.path.exists("data"):
        os.makedirs("data")


def ensure_story_file():
    ensure_data_folder()
    if not os.path.exists(STORY_FILE):
        with open(STORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_stories():
    ensure_story_file()
    try:
        with open(STORY_FILE, "r", encoding="utf-8") as f:
            stories = json.load(f)
        return stories if isinstance(stories, list) else []
    except Exception:
        return []


def save_story(entry):
    stories = load_stories()
    stories.append(entry)
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)


def build_story_prompt(emojis, theme):
    return (
        "Write a short, self-contained English story, about 4–6 sentences. "
        "Style: a modern, global echo of One Thousand and One Nights where any person can be the storyteller. "
        "Do NOT mention Scheherazade or a king. "
        "Begin the first sentence with 'Once' or 'Once upon a time'. "
        "End with a satisfying, closed resolution. "
        "No cliffhanger. No 'to be continued'. "
        "Keep language vivid but simple. "
        f"Inspiration emojis: {emojis}. Theme: {theme}."
    )


def build_image_prompt(emojis, theme):
    return (
        "Create a richly detailed Persian manuscript-style illustration inspired by "
        "Shahnameh miniatures, illuminated Iranian manuscripts, and epic Persian painting. "

        "The artwork should be visually dense, layered, ornate, and full of intricate details. "
        "Use crowded compositions, decorative borders, symbolic creatures, celestial forms, "
        "mythical motifs, floral arabesques, gold illumination, complex textures, "
        "miniature-style spatial flattening, and poetic visual atmosphere. "

        "Avoid clean minimalist portraits or empty compositions. "
        "The image should feel alive, mysterious, ceremonial, excessive, and visually immersive. "

        "Blend traditional Persian miniature aesthetics with subtle surrealism and dreamlike symbolism. "
        "Include ornamental chaos, overlapping decorative elements, handwritten manuscript energy, "
        "and the feeling of an ancient illuminated page discovered in a forgotten archive. "

        "Use deep blues, lapis lazuli tones, gold leaf textures, aged paper feeling, "
        "intricate linework, and elaborate framing. "

        "Use a richer and more varied Persian manuscript palette with luminous lapis blue, "
        "turquoise, emerald green, cinnabar red, saffron orange, warm gold, ivory, and deep ultramarine. "
        "Avoid monochromatic blue-and-gold dominance. "
        "Distribute color accents across the composition like natural mineral pigments in illuminated manuscripts. "
        "Colors should feel layered, aged, painterly, mineral-based, and slightly muted, "
        "not neon, not cartoonish, not digitally saturated. "

        "The artwork should resemble a fragmented illuminated Shahnameh manuscript page "
        "rediscovered from a lost archive. "
        "Include asymmetry, marginalia-like details, hidden creatures, floating ornaments, "
        "miniature crowds, symbolic architecture, poetic visual noise, and layered decorative fields. "

        "The manuscript page should prioritize ornamental atmosphere, symbolic density, "
        "and painterly texture over explicit character depiction. "
        "Human and animal forms should appear partially dissolved into floral patterns, "
        "mineral pigments, smoke-like ornamentation, and layered manuscript textures. "
        "Figures should feel fragmented, miniature-like, symbolic, partially hidden, "
        "and integrated into the page rather than clearly staged subjects. "
        "Avoid theatrical posing, expressive cartoon faces, or readable character illustration. "
        "The image should resemble an ancient illuminated manuscript artifact where narrative elements "
        "emerge slowly from the ornamental surface. "
        "Favor ambiguity, visual rhythm, abstraction, and curatorial sophistication "
        "over direct storytelling clarity. "

        "Avoid clean symmetry or polished portrait photography aesthetics. "
        "Avoid distorted AI faces, photorealism, modern fantasy game aesthetics, "
        "children's book style, or obvious cartoon illustration. "

        "The image should feel like a rare museum-quality illuminated Persian manuscript page, "
        "curated for a contemporary art exhibition. "

        f"Emojis: {emojis}. Theme: {theme}."
    )


def clean_story(story):
    if not story:
        return ""

    story = story.strip()

    if story and not story.lower().startswith(("once ", "once upon a time")):
        story = "Once, " + story[0].lower() + story[1:]

    if story and story[-1] not in ".!?":
        story += "."

    return story


def get_openai_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")

    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_story_with_openai(client, emojis, theme):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise, imaginative writer. "
                    "Your stories always begin with 'Once' or 'Once upon a time' "
                    "and conclude with a clear ending."
                )
            },
            {
                "role": "user",
                "content": build_story_prompt(emojis, theme)
            }
        ],
        temperature=0.9,
        max_tokens=400
    )

    return clean_story(response.choices[0].message.content)


def generate_image_with_openai(client, emojis, theme):
    response = client.images.generate(
        model="gpt-image-1-mini",
        prompt=build_image_prompt(emojis, theme),
        size="1024x1024",
        quality="low",
        n=1
    )

    image_base64 = response.data[0].b64_json

    if not image_base64:
        raise RuntimeError("Image generation returned no image data")

    return "data:image/png;base64," + image_base64


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "openai_key_loaded": bool(OPENAI_API_KEY)
    })


@app.route("/stories", methods=["GET"])
def stories():
    return jsonify(load_stories())


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or request.form.to_dict()

    emojis = (data.get("emojis") or "").strip()
    theme = (data.get("theme") or "").strip()

    if not emojis or not theme:
        return jsonify({
            "error": "Emojis and theme are required"
        }), 400

    try:
        client = get_openai_client()

        story = generate_story_with_openai(client, emojis, theme)
        image_url = generate_image_with_openai(client, emojis, theme)

        save_story({
            "created_at": datetime.utcnow().isoformat() + "Z",
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url
        })

        return jsonify({
            "story": story,
            "image_url": image_url
        })

    except Exception as e:
        print("❌ /generate error:", repr(e))
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
