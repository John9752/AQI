import requests
import os
from dotenv import load_dotenv

load_dotenv()
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

def test_waqi_search(keyword):
    url = f"https://api.waqi.info/search/?keyword={keyword}&token={WAQI_TOKEN}"
    resp = requests.get(url).json()
    print(f"\n--- Search results for '{keyword}' ---")
    if resp.get('status') == 'ok':
        for itm in resp.get('data', []):
            print(f"Station: {itm['station']['name']} (UID: {itm['uid']}, AQI: {itm['aqi']})")
    else:
        print(f"Error: {resp.get('data', 'No status ok')}")

if __name__ == "__main__":
    test_waqi_search("Malkapuram, Visakhapatnam")
    test_waqi_search("Rushikonda, Visakhapatnam")
    test_waqi_search("Visakhapatnam")
