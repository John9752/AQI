import sys
import os
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aqi_fetcher

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITIES = [
    "Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", 
    "Kurnool", "Nellore", "Rajamahendravaram", "Kakinada", 
    "Anantapur", "Chittoor", "Gajuwaka"
]

def collect_data():
    all_records = []
    
    # 30 days back
    end_time = int(time.time())
    start_time = end_time - (30 * 24 * 60 * 60)
    
    print(f"--- Starting AP Data Collection ({len(CITIES)} cities, 30 days) ---")
    
    for city in CITIES:
        print(f"Processing {city}...")
        try:
            # 1. Geocode
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city},AP,IN&limit=1&appid={API_KEY}"
            geo_res = requests.get(geo_url).json()
            if not geo_res:
                print(f"  Geocoding failed for {city}")
                continue
                
            lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
            
            # 2. Fetch History
            hist_url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start_time}&end={end_time}&appid={API_KEY}"
            hist_res = requests.get(hist_url).json()
            
            if 'list' in hist_res:
                print(f"  Found {len(hist_res['list'])} records.")
                for entry in hist_res['list']:
                    comps = entry['components']
                    
                    # Apply Indian Calibration & Industrial Boosters (to match dashboard)
                    calibrated = aqi_fetcher.apply_ground_calibration(comps, 'IN', city)
                    
                    # Calculate Indian AQI for Labeling
                    aqi, level = aqi_fetcher.calculate_indian_aqi(calibrated)
                    
                    # Prepare row
                    record = {
                        'timestamp': entry['dt'],
                        'city': city,
                        'PM2.5': calibrated['pm2_5'],
                        'PM10': calibrated['pm10'],
                        'NO2': calibrated['no2'],
                        'CO': calibrated['co'],
                        'SO2': calibrated['so2'],
                        'O3': calibrated['o3'],
                        'Temperature': 25, # Base assumption for historical weather
                        'Humidity': 60,
                        'AQI': aqi
                    }
                    all_records.append(record)
            
            # Rate limiting safety
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error processing {city}: {e}")

    # 3. Save to CSV
    if all_records:
        df = pd.DataFrame(all_records)
        dataset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dataset')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            
        csv_path = os.path.join(dataset_dir, 'ap_historical.csv')
        df.to_csv(csv_path, index=False)
        print(f"\n✅ Success! Saved {len(all_records)} records to {csv_path}")
    else:
        print("\n❌ No data collected.")

if __name__ == "__main__":
    collect_data()
