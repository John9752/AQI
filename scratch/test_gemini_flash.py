import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
model = "gemini-1.5-flash"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

payload = {
    "contents": [{"parts": [{"text": "Hello, how are you?"}]}]
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
