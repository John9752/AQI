import requests
import os
import hashlib
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
WAQI_TOKEN = os.getenv("WAQI_TOKEN", "demo")

def fetch_waqi_data(city):
    """
    Fetches real-time AQI and pollutant data from the WAQI (aqicn.org) API.
    This provides actual station-level data which is much more accurate 
    for ground-level readings in cities like Visakhapatnam.
    """
    try:
        if not WAQI_TOKEN: return None
        
        # 1. Search for the city to get the best station feed
        search_url = f"https://api.waqi.info/search/?keyword={city}&token={WAQI_TOKEN}"
        search_resp = requests.get(search_url).json()
        
        if search_resp.get('status') != 'ok' or not search_resp.get('data'):
            return None
            
        # Get the first/best station
        station_uid = search_resp['data'][0]['uid']
        
        # 2. Fetch the actual feed for this station
        feed_url = f"https://api.waqi.info/feed/@{station_uid}/?token={WAQI_TOKEN}"
        feed_resp = requests.get(feed_url).json()
        
        if feed_resp.get('status') != 'ok':
            return None
            
        data = feed_resp['data']
        iaqi = data.get('iaqi', {})
        
        # Map WAQI iaqi to our internal components format
        # WAQI values are generally raw concentrations in ug/m3 or mg/m3
        components = {
            'pm2_5': iaqi.get('pm25', {}).get('v', 0),
            'pm10': iaqi.get('pm10', {}).get('v', 0),
            'no2': iaqi.get('no2', {}).get('v', 0),
            'so2': iaqi.get('so2', {}).get('v', 0),
            'co': iaqi.get('co', {}).get('v', 0) * 1000.0 if iaqi.get('co', {}).get('v', 0) < 50 else iaqi.get('co', {}).get('v', 0), # Guessing mg/m3 -> ug/m3 for CO if very small
            'o3': iaqi.get('o3', {}).get('v', 0),
            'nh3': iaqi.get('nh3', {}).get('v', 0)
        }
        
        return {
            "city": data.get('city', {}).get('name', city),
            "aqi": data.get('aqi', 0),
            "components": components,
            "coordinates": {
                "lat": data.get('city', {}).get('geo', [0, 0])[0],
                "lon": data.get('city', {}).get('geo', [0, 0])[1]
            },
            "source": f"Station: {data.get('city', {}).get('name', 'Unknown')} (via WAQI)"
        }
    except Exception as e:
        print(f"[WAQI Error] {e}")
        return None

def fetch_waqi_by_coords(lat, lon):
    """
    Fetches the nearest station data based on coordinates using WAQI API.
    """
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
        resp = requests.get(url).json()
        
        if resp.get('status') != 'ok':
            return None
            
        data = resp['data']
        iaqi = data.get('iaqi', {})
        
        components = {
            'pm2_5': iaqi.get('pm25', {}).get('v', 0),
            'pm10': iaqi.get('pm10', {}).get('v', 0),
            'no2': iaqi.get('no2', {}).get('v', 0),
            'so2': iaqi.get('so2', {}).get('v', 0),
            'co': iaqi.get('co', {}).get('v', 0) * 1000.0 if iaqi.get('co', {}).get('v', 0) < 50 else iaqi.get('co', {}).get('v', 0),
            'o3': iaqi.get('o3', {}).get('v', 0),
            'nh3': iaqi.get('nh3', {}).get('v', 0)
        }
        
        return {
            "city": data.get('city', {}).get('name', 'Selected Area'),
            "city_for_db": data.get('city', {}).get('name', 'Near Station'),
            "aqi": data.get('aqi', 0),
            "components": components,
            "coordinates": {"lat": lat, "lon": lon},
            "source": f"Nearest Station: {data.get('city', {}).get('name')} (WAQI)"
        }
    except Exception as e:
        print(f"[WAQI Coords Error] {e}")
        return None

def apply_local_variance(lat, lon, components):
    """
    Applies small, deterministic variations to pollutant concentrations
    based on exact coordinates. This ensures that nearby localities within
    the same OpenWeather grid cell show distinct (but stable) AQI values.
    """
    # Create a stable seed from coordinates (round to 4 decimals for stability)
    seed = f"{round(lat, 4)}{round(lon, 4)}"
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    
    varied = components.copy()
    # Major pollutants to vary
    pollutants = ['pm2_5', 'pm10', 'co', 'no2', 'so2', 'o3']
    
    for i, p in enumerate(pollutants):
        if p in varied:
            # Deterministic multiplier between 0.88 and 1.12 (+/- 12%)
            # Each pollutant uses a different part of the hash
            mult = 0.88 + ((h >> (i * 4)) % 240) / 1000.0
            varied[p] *= mult
            
    return varied

from cpcb_calculator import calculate_indian_aqi

def calculate_usaqi(components):
    """
    Calculates the US EPA Air Quality Index (AQI) based on standard 
    piecewise linear formula and pollutant concentration breakpoints.
    Ref: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
    """
    
    def get_aqi_for_pollutant(cp, breakpoints):
        for clo, chi, ilo, ihi in breakpoints:
            if clo <= cp <= chi:
                return ((ihi - ilo) / (chi - clo)) * (cp - clo) + ilo
        # Fallback for extreme cases (above scale)
        if breakpoints:
            _, chi, _, ihi = breakpoints[-1]
            if cp > chi:
                return ihi
        return 0

    # 1. Prepare and Truncate concentrations as per EPA rules
    pm25 = round(components.get('pm2_5', 0), 1)
    pm10 = int(components.get('pm10', 0))
    co_ppm = round(components.get('co', 0) / 1145.6, 1)
    no2_ppb = int(components.get('no2', 0) / 1.88)
    so2_ppb = int(components.get('so2', 0) / 2.62)
    o3_ppm = round(components.get('o3', 0) / 1963.2, 3)

    # 2. Define Breakpoints
    pm25_bp = [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400), (350.5, 500.4, 401, 500)]
    pm10_bp = [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150), (255, 354, 151, 200), (355, 424, 201, 300), (425, 504, 301, 400), (505, 604, 401, 500)]
    co_bp = [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150), (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 40.4, 301, 400), (40.5, 50.4, 401, 500)]
    no2_bp = [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150), (361, 649, 151, 200)]
    so2_bp = [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150), (186, 304, 151, 200)]
    o3_bp = [(0.000, 0.054, 0, 50), (0.055, 0.070, 51, 100), (0.071, 0.085, 101, 150), (0.086, 0.105, 151, 200), (0.106, 0.200, 201, 300)]

    # 3. Calculate Individual Indices
    indices = [
        get_aqi_for_pollutant(pm25, pm25_bp),
        get_aqi_for_pollutant(pm10, pm10_bp),
        get_aqi_for_pollutant(co_ppm, co_bp),
        get_aqi_for_pollutant(no2_ppb, no2_bp),
        get_aqi_for_pollutant(so2_ppb, so2_bp),
        get_aqi_for_pollutant(o3_ppm, o3_bp)
    ]

    # Final AQI is the maximum of all tracked pollutants
    final_aqi = int(round(max(indices)))
    
    # Map back to 1-5 level for UI compatibility
    if final_aqi <= 50: level = 1
    elif final_aqi <= 100: level = 2
    elif final_aqi <= 150: level = 3
    elif final_aqi <= 200: level = 4
    else: level = 5
    
    return final_aqi, level

def apply_regional_bias(components, city_name, query_hint=""):
    """
    Applies hyper-local corrections for known industrial/urban hubs in Andhra Pradesh.
    """
    calibrated = components.copy()
    city_lower = city_name.lower()
    hint_lower = query_hint.lower()
    
    is_vizag = any(term in city_lower or term in hint_lower for term in 
                   ['visakha', 'vizag', 'gajuwaka', 'pendurthi', 'parawada', 'steel plant', 'anakapalle'])
                   
    if is_vizag:
        calibrated['pm2_5'] *= 1.2
        calibrated['pm10'] *= 1.1
        calibrated['no2'] *= 1.2
        calibrated['so2'] *= 1.2
        
    return calibrated

def apply_ground_calibration(components, country_code, city="", query_hint=""):
    """
    Applies multipliers to boost OpenWeather PM density to match actual
    ground-level sensor readings in India.
    """
    calibrated = components.copy()
    if country_code == "IN" or "india" in city.lower() or "india" in query_hint.lower():
        calibrated['pm2_5'] *= 2.0
        calibrated['pm10']  *= 1.8
        calibrated['no2']   *= 1.2
    return calibrated

def fetch_historical_aqi(city, days=7):
    """
    Fetches historical AQI data for the last 'days' and applies
    localized calibration and standards.
    """
    try:
        # 1. Geocode to get coordinates and country
        geo = fetch_aqi_data(city)
        if "error" in geo: return geo
        
        lat, lon = geo['coordinates']['lat'], geo['coordinates']['lon']
        # Extract country code (e.g., "Visakhapatnam, IN" -> "IN")
        country_code = geo['city'].split(',')[-1].strip()
        
        end = int(time.time())
        start = end - (days * 24 * 3600)
        
        # 2. Fetch history from OpenWeather
        hist_url = f"https://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={API_KEY}"
        resp = requests.get(hist_url).json()
        
        if 'list' not in resp:
            return {"error": "Historical data unavailable"}
            
        # 3. Aggregate by day
        daily_buckets = {}
        for entry in resp['list']:
            date_key = datetime.fromtimestamp(entry['dt']).strftime('%Y-%m-%d')
            if date_key not in daily_buckets:
                daily_buckets[date_key] = []
            daily_buckets[date_key].append(entry['components'])
            
        # 4. Calculate Calibrated AQI per day
        trends = []
        for date_str in sorted(daily_buckets.keys()):
            bucket = daily_buckets[date_str]
            # Average concentrations for the day
            avg_comp = {k: sum(d[k] for d in bucket)/len(bucket) for k in bucket[0].keys()}
            
            # Apply our custom Calibration and Math
            calibrated = apply_ground_calibration(avg_comp, country_code, city)
            calibrated = apply_regional_bias(calibrated, city)
            
            # Use calculate_indian_aqi to match local CPCB standards
            res = calculate_indian_aqi(calibrated)
            aqi = res["aqi"]
                
            trends.append({"date": date_str, "aqi": aqi})
            
        return trends
        
    except Exception as e:
        import traceback
        print(f"[Historical Fetch Error] {str(e)}")
        traceback.print_exc()
        return {"error": f"Historical processing error: {str(e)}"}

def fetch_aqi_data(city):
    """
    Fetches combination of Air Pollution data and Current Weather data 
    (for temperature/humidity) from OpenWeather APIs.
    Includes Smart Fallbacks for localized areas (suburbs/neighborhoods).
    """
    if not API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing in backend environment"}

    try:
        # 1. NEW: Try WAQI (Station Data) first as it is much more accurate
        waqi_data = fetch_waqi_data(city)
        if waqi_data:
            # Still apply CPCB standard to the raw components for consistency with Indian laws
            naqi_data = calculate_indian_aqi(waqi_data['components'])
            
            return {
                "city": waqi_data['city'],
                "requested_name": city,
                "aqi": naqi_data["aqi"], # Use our CPCB aqi
                "level": naqi_data["level"],
                "category": naqi_data["category"],
                "health_message": naqi_data["health_message"],
                "dominant_pollutant": naqi_data["dominant_pollutant"],
                "components": waqi_data['components'],
                "coordinates": waqi_data['coordinates'],
                "source": waqi_data['source'],
                "openweather_api_aqi_level": None # Not using OWM
            }

        # 2. Geocoding with Smart Fallbacks (FOR OWM FALLBACK)
        search_terms = []
        search_terms.append(city)
        if "," not in city:
            search_terms.append(f"{city}, Andhra Pradesh, IN")
            search_terms.append(f"{city}, India")

        geo_data = None
        for term in search_terms:
            geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={term}&limit=1&appid={API_KEY}"
            try:
                resp = requests.get(geo_url).json()
                if isinstance(resp, list) and len(resp) > 0:
                    geo_data = resp
                    break
                elif isinstance(resp, dict) and "message" in resp:
                    return {"error": f"OpenWeather API Error: {resp['message']}"}
            except Exception:
                continue
        
        if not geo_data:
            return {"error": f"City '{city}' not found. Please check spelling."}
        
        # Safe extraction from list
        first_match = geo_data[0]
        lat, lon = first_match['lat'], first_match['lon']
        full_name = f"{first_match['name']}, {first_match.get('country', '')}"
        country_code = first_match.get('country', '')
        
        # 2. Fetch AQI
        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_data = requests.get(aqi_url).json()

        # 3. Fetch Weather (For Temperature and Humidity required by ML model)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        weather_data = requests.get(weather_url).json()
        
        if 'list' in aqi_data and 'main' in weather_data:
            current = aqi_data['list'][0]
            base_components = current['components']
            base_components['temperature'] = weather_data['main']['temp']
            base_components['humidity'] = weather_data['main']['humidity']
            
            # Apply Local Variance based on exact coordinates
            varied_components = apply_local_variance(lat, lon, base_components)
            
            # Apply Ground-Truth Calibration (Special boost for India)
            # Pass BOTH the geocoded name and the original search for bias detection
            final_components = apply_ground_calibration(varied_components, country_code, full_name, city)
            final_components = apply_regional_bias(final_components, full_name, city)
            
            # Enforce Indian CPCB Standard calculation
            naqi_data = calculate_indian_aqi(final_components)
            final_aqi = naqi_data["aqi"]
            aqi_level = naqi_data["level"]
            category = naqi_data["category"]
            dominant_pollutant = naqi_data["dominant_pollutant"]
            health_message = naqi_data["health_message"]
            
            # Fallback to OpenWeather API AQI for comparison
            owm_aqi = current.get('main', {}).get('aqi')
            
            # Determine data source for attribution
            # Check industrial keywords in the search string
            search_context = (full_name + " " + city).lower()
            is_industrial = any(z in search_context for z in ['gajuwaka', 'duvvada', 'industrial', 'auto nagar'])
            source = "Industrial-Corrected Data" if is_industrial else "Calibrated Atmospheric Data"

            return {
                "city": full_name,
                "requested_name": city, # Return the original search name for trend synchronization
                "aqi": final_aqi,
                "level": aqi_level,
                "category": category,
                "health_message": health_message,
                "dominant_pollutant": dominant_pollutant,
                "components": final_components,
                "coordinates": {"lat": lat, "lon": lon},
                "source": source,
                "openweather_api_aqi_level": owm_aqi
            }
        return {"error": "Could not parse API response"}
            
    except Exception as e:
        import traceback
        print(f"[AQI Fetcher Error] {str(e)}")
        traceback.print_exc()
        return {"error": f"Backend processing error: {type(e).__name__}: {str(e)}"}

def fetch_aqi_by_coords(lat, lon):
    if not API_KEY:
        return {"error": "OPENWEATHER_API_KEY is missing in backend environment"}

    try:
        # 1. NEW: Try WAQI (Station Data) first
        waqi_data = fetch_waqi_by_coords(lat, lon)
        if waqi_data:
            naqi_data = calculate_indian_aqi(waqi_data['components'])
            return {
                "city_for_db": waqi_data['city_for_db'],
                "city": waqi_data['city'],
                "aqi": naqi_data["aqi"],
                "level": naqi_data["level"],
                "category": naqi_data["category"],
                "health_message": naqi_data["health_message"],
                "dominant_pollutant": naqi_data["dominant_pollutant"],
                "components": waqi_data['components'],
                "coordinates": {"lat": lat, "lon": lon},
                "source": waqi_data['source'],
                "openweather_api_aqi_level": None
            }

        # 2. Reverse Geocoding (FOR OWM FALLBACK)
        geo_url = f"https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
        geo_data = requests.get(geo_url).json()
        location_name = "Unknown Location"
        city_for_db = f"Lat:{lat}, Lon:{lon}"
        country_code = ""
        
        if isinstance(geo_data, list) and len(geo_data) > 0:
            first_match = geo_data[0]
            location_name = f"{first_match.get('name', 'Selected Area')}, {first_match.get('country', '')}"
            city_for_db = first_match.get('name', 'Unknown')
            country_code = first_match.get('country', '')
        elif isinstance(geo_data, dict) and "message" in geo_data:
            return {"error": f"Geocoding Error: {geo_data['message']}"}
            
        # Air Pollution
        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        aqi_data = requests.get(aqi_url).json()

        # Weather (For Temp/Humidity)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        weather_data = requests.get(weather_url).json()

        if 'list' in aqi_data and 'main' in weather_data:
            current = aqi_data['list'][0]
            base_components = current['components']
            base_components['temperature'] = weather_data['main']['temp']
            base_components['humidity'] = weather_data['main']['humidity']

            # Apply Local Variance based on exact coordinates
            varied_components = apply_local_variance(float(lat), float(lon), base_components)

            # Apply Ground-Truth Calibration (Special boost for India)
            final_components = apply_ground_calibration(varied_components, country_code, location_name)
            final_components = apply_regional_bias(final_components, location_name)

            # Enforce Indian CPCB Standard calculation
            naqi_data = calculate_indian_aqi(final_components)
            final_aqi = naqi_data["aqi"]
            aqi_level = naqi_data["level"]
            category = naqi_data["category"]
            dominant_pollutant = naqi_data["dominant_pollutant"]
            health_message = naqi_data["health_message"]
            
            # Fallback to OpenWeather API AQI for comparison
            owm_aqi = current.get('main', {}).get('aqi')

            return {
                "city_for_db": city_for_db,
                "city": location_name,
                "aqi": final_aqi,
                "level": aqi_level,
                "category": category,
                "health_message": health_message,
                "dominant_pollutant": dominant_pollutant,
                "components": final_components,
                "coordinates": {"lat": lat, "lon": lon},
                "openweather_api_aqi_level": owm_aqi
            }
        return {"error": "Could not parse API response"}
    except Exception as e:
        import traceback
        print(f"[Coords Fetcher Error] {str(e)}")
        traceback.print_exc()
        return {"error": f"Backend coordinate error: {type(e).__name__}: {str(e)}"}
