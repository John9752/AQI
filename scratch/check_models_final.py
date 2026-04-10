import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
models = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']

print(f"Testing models with API Key: {api_key[:5]}...")

for m in models:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}'
    try:
        r = requests.post(url, json={'contents': [{'parts': [{'text': 'hi'}]}]}, timeout=10)
        print(f"{m}: {r.status_code}")
        if r.status_code != 200:
            print(f"  Error: {r.text[:200]}")
        else:
            print(f"  Success!")
    except Exception as e:
        print(f"{m}: Exception - {e}")
