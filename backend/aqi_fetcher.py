import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def fetch_aqi_data(city):
    """
    Fetches combination of Air Pollution data and Current Weather data 
    (for temperature/humidity) from OpenWeather APIs.
    """
    try:
        # 1. Geocoding
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
        geo_data = requests.get(geo_url).json()
        if not geo_data:
            return {"error": "City not found"}
        
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
        full_name = f"{geo_data[0]['name']}, {geo_data[0].get('country', '')}"
        
        # 2. Fetch AQI
        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_data = requests.get(aqi_url).json()

        # 3. Fetch Weather (For Temperature and Humidity required by ML model)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        weather_data = requests.get(weather_url).json()
        
        if 'list' in aqi_data and 'main' in weather_data:
            current = aqi_data['list'][0]
            aqi_level = current['main']['aqi']
            # Simulated 0-500 scale for realistic display
            simulated_aqi = [42, 75, 120, 170, 250][aqi_level-1]
            
            components = current['components']
            # Append Temperature and Humidity to components dict so database & ML logic flows easily
            components['temperature'] = weather_data['main']['temp']
            components['humidity'] = weather_data['main']['humidity']
            
            return {
                "city": full_name,
                "aqi": simulated_aqi,
                "level": aqi_level,
                "components": components,
                "coordinates": {"lat": lat, "lon": lon}
            }
        return {"error": "Could not parse API response"}
            
    except Exception as e:
        return {"error": str(e)}

def fetch_aqi_by_coords(lat, lon):
    try:
        # Reverse Geocoding
        geo_url = f"https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
        geo_data = requests.get(geo_url).json()
        location_name = "Unknown Location"
        city_for_db = f"Lat:{lat}, Lon:{lon}"
        if geo_data:
            location_name = f"{geo_data[0].get('name', 'Selected Area')}, {geo_data[0].get('country', '')}"
            city_for_db = geo_data[0].get('name', 'Unknown')
            
        # Air Pollution
        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_data = requests.get(aqi_url).json()

        # Weather (For Temp/Humidity)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        weather_data = requests.get(weather_url).json()

        if 'list' in aqi_data and 'main' in weather_data:
            current = aqi_data['list'][0]
            aqi_level = current['main']['aqi']
            simulated_aqi = [42, 75, 120, 170, 250][aqi_level-1]
            components = current['components']
            components['temperature'] = weather_data['main']['temp']
            components['humidity'] = weather_data['main']['humidity']

            return {
                "city_for_db": city_for_db,
                "city": location_name,
                "aqi": simulated_aqi,
                "level": aqi_level,
                "components": components,
                "coordinates": {"lat": lat, "lon": lon}
            }
        return {"error": "Could not parse API response"}
    except Exception as e:
        return {"error": str(e)}
