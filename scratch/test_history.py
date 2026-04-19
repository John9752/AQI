import sys
import os
import json
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

import aqi_fetcher

def test_history():
    print("--- Testing Historical AQI Fetcher ---")
    city = "Visakhapatnam"
    print(f"Fetching 7-day history for: {city}")
    
    history = aqi_fetcher.fetch_historical_aqi(city)
    
    if "error" in history:
        print(f"❌ Error: {history['error']}")
        return

    print(f"Received {len(history)} days of data.")
    for entry in history:
        print(f"  - {entry['date']}: AQI {entry['aqi']}")

    # Check for Indian Calibration
    # PM2.5 and PM10 should be significantly higher than raw satellite data
    print("\n--- Calibration Check ---")
    print("History points should reflect the 3.5x boost + 15 offset implemented for India.")

if __name__ == "__main__":
    load_dotenv()
    test_history()
