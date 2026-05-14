from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

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

        if isinstance(stories, list):
            return stories

        return []

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
        f"""
Create an intricate Persian manuscript-style painting inspired by
Safavid miniature art, Shahnameh illustrations,
and the compositional atmosphere of Kamāl al-Dīn Behzād.

The result should feel balanced BETWEEN abstraction and recognizable narrative.

Important:
The image should NOT become:
- too abstract and psychedelic
- too modern or digital
- too clean and figurative
- too cartoonish
- too symbolic-only

Target aesthetic:
A poetic Persian miniature with semi-recognizable figures and dense ornamentation.

Composition:
- crowded manuscript-page composition
- layered storytelling scenes
- intertwined humans, animals, plants, clouds, architecture
- intricate Persian borders and illuminated framing
- decorative density across the whole image
- visual richness and movement
- miniature-style flat spatial perspective
- subtle ambiguity and painterly abstraction
- detailed textures and ornamental rhythm

Figures:
- figures should be partially stylized and slightly abstracted
- faces soft, expressive, but not hyper-detailed
- anatomy miniature-like rather than realistic
- figures integrated into patterns and environment
- emotional storytelling without looking like cartoons

Color palette:
- rich lapis blue
- glowing turquoise
- crimson red
- malachite green
- saffron yellow
- burnished gold
- copper orange
- jewel-toned Persian manuscript colors
- strong but elegant contrast
- luminous mineral pigment appearance

Texture and mood:
- aged illuminated manuscript
- handmade brush texture
- layered pigment feel
- ornamental complexity
- mystical and poetic atmosphere
- visually immersive and dense

Style balance:
50% authentic Persian miniature narrative painting
50% poetic ornamental abstraction

Avoid:
- psychedelic neon abstraction
- cartoon style
- Disney expressions
- modern fantasy concept art
- minimalist empty scenes
- obvious AI symmetry
- photographic realism
- clean vector illustration
- isolated centered portrait compositions

The emojis and theme should appear symbolically and naturally woven into the scene.

Emojis: {emojis}
Theme: {theme}
"""
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
        raise RuntimeError(
            "OPENAI_API_KEY is missing in Render Environment Variables"
        )

    from openai import OpenAI
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_story_with_openai(client, emojis, theme):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise imaginative writer. "
                    "Your stories always begin with 'Once' or "
                    "'Once upon a time' and end clearly."
                )
            },
            {
                "role": "user",
                "content": build_story_prompt(emojis, theme)
            }
        ],
        temperature=0.95,
        max_tokens=400
    )

    story = response.choices[0].message.content
    return clean_story(story)


def generate_image_with_openai(client, emojis, theme):
    prompt = build_image_prompt(emojis, theme)

    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="medium",
        n=1
    )

    image_base64 = response.data[0].b64_json

    if not image_base64:
        raise RuntimeError("Image generation failed")

    return f"data:image/png;base64,{image_base64}"


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

        story = generate_story_with_openai(
            client,
            emojis,
            theme
        )

        image_url = generate_image_with_openai(
            client,
            emojis,
            theme
        )

        result = {
            "story": story,
            "image_url": image_url
        }

        save_story({
            "created_at": datetime.utcnow().isoformat() + "Z",
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url
        })

        return jsonify(result)

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