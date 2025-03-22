import openai
import os

# Make sure to load your OpenAI API key correctly from your environment
# Or hardcode your key if not using .env
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # Make sure you're using a model that's available to you
    messages=[{"role": "user", "content": "Tell me a story with emojis: 😎🎉"}]
)

# Print out the response to see if the request works correctly
print(response.choices[0]['message']['content'])
