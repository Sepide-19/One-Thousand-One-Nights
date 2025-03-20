import openai
from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
from flask_cors import CORS

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

app = Flask(__name__)
CORS(app)  # اضافه کردن CORS به اپلیکیشن برای اجازه دادن به درخواست‌های خارجی

# بارگذاری API Key از متغیر محیطی
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.json
    emojis = data.get('emojis')
    theme = data.get('theme')

    # بررسی ورودی‌ها
    if not emojis or not theme:
        return jsonify({'error': 'Emojis and theme are required'}), 400

    # ساخت prompt برای ارسال به OpenAI
    prompt = f"Generate a story with the following emojis: {emojis} and theme: {theme}"

    try:
        # ارسال درخواست به OpenAI برای تولید داستان
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # مدل استفاده شده
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        story = response['choices'][0]['message']['content'].strip()

        # ایجاد تصویر بر اساس داستان تولید شده
        image_response = openai.Image.create(
            prompt=story,
            n=1,
            size="1024x1024"
        )
        image_url = image_response['data'][0]['url']

        return jsonify({'story': story, 'image_url': image_url})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save_content():
    data = request.json
    story = data.get('story')
    image_url = data.get('image_url')

    # بررسی ورودی‌ها
    if not story or not image_url:
        return jsonify({'error': 'Story and image URL are required'}), 400

    # ذخیره کردن محتوا در فایل (یا پایگاه داده)
    with open('saved_stories.txt', 'a') as f:
        f.write(f"Story: {story}\nImage: {image_url}\n\n")

    return jsonify({'message': 'Content saved successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


