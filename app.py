from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
import os
import openai

# بارگذاری .env
load_dotenv()

# تنظیم اپ
app = Flask(__name__)
CORS(app)

# کلید API
openai.api_key = os.getenv("OPENAI_API_KEY")

# صفحه‌ی اصلی
@app.route('/')
def index():
    return render_template('index.html')

# تولید داستان و تصویر بدون ذخیره‌سازی
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    emojis = data.get('emojis', '')
    theme = data.get('theme', '')

    if not emojis or not theme:
        return jsonify({'error': 'Emojis and theme are required'}), 400

    try:
        # تولید داستان
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

        # تولید تصویر
        image_prompt = f"Create a beautiful image in the style of Persian miniature or Iranian traditional art, based on emojis: {emojis} and theme: {theme}."
        image_response = openai.Image.create(
            prompt=image_prompt,
            n=1,
            size="512x512"
        )
        image_url = image_response["data"][0]["url"]

        return jsonify({"story": story, "image_url": image_url})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": str(e)}), 500

# اجرا
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)



