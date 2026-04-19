import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")
url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat=17.6868&lon=83.2185&appid={api_key}"
r = requests.get(url).json()

with open('owm_test.json', 'w') as f:
    json.dump(r, f)
