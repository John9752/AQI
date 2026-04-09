import requests

API_KEY = "7043c3640e66d3597e3b33ba25117bfe"
city = "New York"
geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"

try:
    response = requests.get(geo_url)
    print(f"Status: {response.status_code}")
    print(f"Data: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
