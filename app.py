import os
import json
import openai
from flask import Flask, render_template, request, jsonify

# اگر می‌خوای مستقیم تست کنی، کلید رو اینجا بنویس (بعداً امنش می‌کنیم)
openai.api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

STORY_FILE = "data/stories.json"

# تابع برای ذخیره داستان‌ها و تصاویر


def save_story(data):
    if not os.path.exists(STORY_FILE):
        with open(STORY_FILE, "w") as f:
            json.dump([], f)

    with open(STORY_FILE, "r") as f:
        all_stories = json.load(f)

    all_stories.append(data)

    with open(STORY_FILE, "w") as f:
        json.dump(all_stories, f, indent=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    emojis = data.get('emojis', '')
    theme = data.get('theme', '')

    try:
        # تولید داستان با gpt-3.5-turbo
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative story writer."},
                {"role": "user", "content": f"Write a short story in English based on these emojis: {emojis}. Theme: {theme}."}
            ],
            max_tokens=500
        )
        story = response["choices"][0]["message"]["content"].strip()

        # تولید تصویر با DALL·E
        image_prompt = f"Create a beautiful image in the style of Persian miniature or Iranian traditional art, based on emojis: {emojis} and theme: {theme}."

        image_response = openai.Image.create(
            prompt=image_prompt,
            n=1,
            size="512x512"
        )
        image_url = image_response["data"][0]["url"]

        result = {"story": story, "image_url": image_url}

        # ذخیره در فایل
        save_story({
            "emojis": emojis,
            "theme": theme,
            "story": story,
            "image_url": image_url
        })

        return jsonify(result)

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
