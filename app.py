import openai
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# استفاده از کلید API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/generate', methods=['POST'])
def generate_content():
    data = request.json
    emojis = data.get('emojis')
    theme = data.get('theme')

    if not emojis or not theme:
        return jsonify({'error': 'Emojis and theme are required'}), 400

    # ایجاد درخواست برای تولید داستان
    prompt = f"Generate a story with the following emojis: {emojis} and theme: {theme}"

    try:
        # استفاده از متد جدید openai.Completion.create()
        response = openai.Completion.create(
            model="gpt-3.5-turbo",  # مدل استفاده شده
            prompt=prompt,
            max_tokens=200
        )
        story = response['choices'][0]['text'].strip()

        # ایجاد تصویر از داستان
        image_response = openai.Image.create(
            prompt=story,
            n=1,
            size="1024x1024"
        )
        image_url = image_response['data'][0]['url']

        return jsonify({'story': story, 'image_url': image_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)





