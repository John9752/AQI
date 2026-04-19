import requests
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from aqi_fetcher import calculate_usaqi, apply_local_variance

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def check_location(city_query):
    print(f"\nChecking: {city_query}")
    # 1. Geocoding
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city_query}&limit=1&appid={API_KEY}"
    geo_data = requests.get(geo_url).json()
    if not geo_data:
        print("  Result: Not found")
        return
    
    lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
    full_name = f"{geo_data[0]['name']}, {geo_data[0].get('country', '')}"
    print(f"  Coordinates: {lat}, {lon}")
    # print(f"  Name: {full_name}")

    # 2. Air Pollution
    aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    aqi_data = requests.get(aqi_url).json()
    
    if 'list' in aqi_data:
        base_components = aqi_data['list'][0]['components']
        
        # Apply the new variance logic
        final_components = apply_local_variance(lat, lon, base_components)
        aqi, level = calculate_usaqi(final_components)
        
        print(f"  Final AQI: {aqi} (Level {level})")
        print(f"  PM2.5 (original): {base_components['pm2_5']} -> (varied): {round(final_components['pm2_5'], 2)}")
    else:
        print("  Error fetching AQI")

if __name__ == "__main__":
    locations = [
        "Visakhapatnam",
        "Gajuwaka, Visakhapatnam",
        "MVP Colony, Visakhapatnam",
        "Madhurawada, Visakhapatnam"
    ]
    for loc in locations:
        check_location(loc)
