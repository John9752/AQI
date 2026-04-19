import requests
import time
import sqlite3

BASE_URL = "http://localhost:8888"

def test_trend_flow():
    city = "Berlin"
    print(f"--- Simulating Dashboard flow for {city} ---")
    
    # 1. Fetch current AQI (triggering a save in DB)
    resp = requests.get(f"{BASE_URL}/get_aqi?city={city}")
    data = resp.json()
    full_name = data.get('city')
    print(f"API returned full name: {full_name}")
    
    if not full_name:
        print("Error: Could not get city name from API")
        return

    # 2. Wait a second for DB to sync (though SQLite is usually instant)
    time.sleep(1)

    # 3. Fetch trends using the returned full name (this is what the fix does)
    print(f"Fetching trends for: {full_name}")
    trend_resp = requests.get(f"{BASE_URL}/aqi_trends?city={full_name}")
    trends = trend_resp.json()
    
    print(f"Trends received: {len(trends)} records")
    if len(trends) > 0:
        print(f"Success! First record: {trends[0]}")
    else:
        print("Failure: No trends found for full name.")
    
    # 4. Also check the 'old' behavior (which we fixed) to show why it failed
    print(f"Checking old behavior (fetching 'Berlin' instead of '{full_name}')...")
    old_trend_resp = requests.get(f"{BASE_URL}/aqi_trends?city={city}")
    old_trends = old_trend_resp.json()
    print(f"Old style trends received: {len(old_trends)} records")

if __name__ == "__main__":
    try:
        test_trend_flow()
    except Exception as e:
        print(f"Test failed: {e}")
