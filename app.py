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
Create a museum-quality contemporary Persian miniature painting
inspired by illuminated Iranian manuscripts and Shahnameh visual culture.

The artwork should feel genuinely artistic and curatorial —
like a contemporary artwork shown at a biennale or major museum exhibition,
NOT fantasy illustration, NOT cartoon, NOT decorative AI art.

The image should balance:
- narrative clarity
- painterly abstraction
- emotional atmosphere
- ornamental density
- sophisticated color relationships

Visual language:
- layered miniature composition
- dense ornamental space
- poetic visual storytelling
- fragmented narrative scenes
- symbolic architecture and gardens
- manuscript borders and illuminated framing
- flowing Persian cloud motifs
- intertwined humans, animals, plants, textiles
- subtle visual chaos and movement
- asymmetrical composition
- tactile painterly surfaces

Very important:
Each generated image should feel visually UNIQUE,
with changing compositions, changing palettes,
changing spatial rhythms, and changing emotional tone.

Do NOT repeat the same dark blue palette every time.

Color direction:
Use richer and more adventurous Persian miniature palettes:
- lapis blue
- turquoise
- emerald green
- deep crimson
- saffron yellow
- rose pink
- burnt orange
- copper
- gold leaf tones
- ivory
- smoky indigo
- pomegranate red

Colors should feel luminous, layered, mineral, and painterly —
not flat or monochromatic.

Some images may be:
- warmer
- greener
- more golden
- more turquoise
- dusk-toned
- rose-toned
- jewel-toned

The palette should evolve naturally from the mood of the story.

Figures:
- semi-recognizable figures
- understated expressions
- elongated miniature-like anatomy
- poetic gestures
- partially absorbed into texture and ornament
- no cartoon smiles
- no theatrical posing

Texture:
- layered pigments
- aged manuscript texture
- delicate brushwork
- hand-painted imperfections
- subtle grain
- visible painterly depth

Mood:
- contemplative
- mystical
- emotionally intelligent
- poetic
- culturally grounded
- visually immersive

Avoid:
- cartoon aesthetics
- children's-book illustration
- obvious AI symmetry
- fantasy concept art
- poster design
- psychedelic neon abstraction
- repetitive compositions
- monochromatic blue-only palettes
- hyper-clean rendering
- photorealism

The emojis and theme should appear subtly and symbolically,
woven naturally into the manuscript world rather than illustrated literally.

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