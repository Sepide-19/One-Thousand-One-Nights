from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import json
import openai
import requests
from datetime import datetime

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# ساخت اپ Flask و تنظیمات
app = Flask(__name__)
CORS(app)

# استفاده از کلید API
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# روت صفحه‌ی اصلی
@app.route('/')
def index():
    return render_template('index.html')

# روت تولید داستان و تصویر
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    emojis = data.get('emojis', '')
    theme = data.get('theme', '')

    if not emojis or not theme:
        return jsonify({'error': 'Emojis and theme are required'}), 400

    try:
        # تولید داستان با GPT
        story_prompt = f"Write a short story in English based on these emojis: {emojis}. Theme: {theme}."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative story writer."},
                {"role": "user", "content": story_prompt}
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

        # 📥 دانلود و ذخیره‌سازی تصویر
        image_data = requests.get(image_url).content
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        image_filename = f"image_{timestamp}.png"
        image_path = os.path.join("static", "images", image_filename)

        with open(image_path, "wb") as f:
            f.write(image_data)

        # آدرس جدید برای استفاده در فرانت‌اند
        image_url = f"/static/images/{image_filename}"

        result = {"story": story, "image_url": image_url}

        # ذخیره داستان در فایل
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

# اجرای برنامه
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

