import requests
import os
from dotenv import load_dotenv

load_dotenv()
WAQI_TOKEN = os.getenv("WAQI_TOKEN")

def test_waqi_feed(uid):
    url = f"https://api.waqi.info/feed/@{uid}/?token={WAQI_TOKEN}"
    resp = requests.get(url).json()
    print(f"\n--- Feed for UID {uid} ---")
    if resp.get('status') == 'ok':
        data = resp['data']
        print(f"Station: {data['city']['name']}")
        print(f"Overall AQI: {data['aqi']}")
        print("IAQI Pollutants:")
        for k, v in data.get('iaqi', {}).items():
            print(f"  {k}: {v}")
    else:
        print(f"Error: {resp}")

if __name__ == "__main__":
    # GVM Corporation
    test_waqi_feed(12443)
    # GVMC Ram Nagar (if search returns it)
    test_waqi_feed(9067)
