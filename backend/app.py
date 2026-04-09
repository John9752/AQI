from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
import sys
import requests

# Import our new modules
import database
import aqi_fetcher
import email_service

# Setup model import path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'ml_model'))
from train_model import predict_aqi as ml_predict_aqi

app = Flask(__name__, static_url_path='', static_folder=BASE_DIR)
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return app.send_static_file(path)

# Initialize Database
database.init_db()

# CONFIGURATION mapping
AQI_MAPPING = {
    1: {"name": "Good", "rec": "Air quality is satisfactory. Ideal for outdoor activities."},
    2: {"name": "Fair", "rec": "Sensitive people should consider limiting prolonged outdoor exertion."},
    3: {"name": "Moderate", "rec": "Sensitive groups may experience health effects. Limit outdoor exertion."},
    4: {"name": "Poor", "rec": "Health alert! Avoid outdoor activities and wear protective masks."},
    5: {"name": "Very Poor", "rec": "Health warnings of emergency conditions. Stay indoors."}
}

# ==========================================
# BACKGROUND MONITORING LOGIC
# ==========================================
def monitor_aqi_background():
    while True:
        print("[Monitor] Checking AQI for subscribers...")
        subs = database.get_subscriptions()
        checked_cities = {}

        for email, city, threshold, last_alert in subs:
            try:
                if city not in checked_cities:
                    data = aqi_fetcher.fetch_aqi_data(city)
                    if "error" not in data:
                        city_data = data
                        checked_cities[city] = city_data
                        # Save to trend history using new schema
                        database.save_aqi_reading(city_data['city'], city_data['aqi'], city_data['components'])

                # Check alert
                if city in checked_cities:
                    city_data = checked_cities[city]
                    simulated_aqi = city_data['aqi']
                    aqi_level = city_data['level']
                    if simulated_aqi >= threshold:
                        mapping = AQI_MAPPING.get(aqi_level, AQI_MAPPING[5])
                        email_service.send_aqi_alert(
                            email, city, simulated_aqi, 
                            mapping['name'], mapping['rec']
                        )
            except Exception as e:
                print(f"[Monitor] Error processing alert for {email}: {e}")

        # Wait for 30 minutes
        time.sleep(1800)

if not any(t.name == "AQIMonitor" for t in threading.enumerate()):
    monitor_thread = threading.Thread(target=monitor_aqi_background, name="AQIMonitor", daemon=True)
    monitor_thread.start()

# ==========================================
# API ENDPOINTS (Legacy support for frontend)
# ==========================================
@app.route('/get_aqi', methods=['GET'])
def get_aqi_legacy():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    data = aqi_fetcher.fetch_aqi_data(city)
    if "error" not in data:
        database.save_aqi_reading(data['city'], data['aqi'], data['components'])
        return jsonify(data)
    return jsonify(data), 500

@app.route('/get_aqi_coords', methods=['GET'])
def get_aqi_coords_legacy():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"error": "Latitude and longitude are required"}), 400
    data = aqi_fetcher.fetch_aqi_by_coords(lat, lon)
    if "error" not in data:
        database.save_aqi_reading(data.pop('city_for_db', data['city']), data['aqi'], data['components'])
        return jsonify(data)
    return jsonify(data), 500

@app.route('/aqi_trends', methods=['GET'])
def aqi_trends_legacy():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    trends = database.get_aqi_trends(city)
    return jsonify(trends)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')
    city = data.get('city')
    threshold = data.get('threshold', 101)
    if not email or not city:
        return jsonify({"success": False, "message": "Email and City are required"}), 400
    success = database.add_subscription(email, city, threshold)
    if success:
        return jsonify({"success": True, "message": "Successfully subscribed to alerts"})
    return jsonify({"success": False, "message": "Subscription failed"}), 500

@app.route('/send_welcome', methods=['POST'])
def send_welcome():
    data = request.json
    success = email_service.send_welcome_email(data.get('email'), data.get('name'))
    if success:
        return jsonify({"success": True, "message": "Welcome email sent"})
    return jsonify({"success": False, "message": "Failed to send welcome email"}), 500

@app.route('/get_user_preferences', methods=['GET'])
def get_user_preferences():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    subs = database.get_subscriptions()
    for row in subs:
        if row[0] == email:
            return jsonify({"city": row[1], "threshold": row[2]})
    return jsonify({"city": "New York", "threshold": 101})

# ==========================================
# NEW REQUIRED ENDPOINTS (For ML and Data Fetching)
# ==========================================
@app.route('/get_current_aqi', methods=['GET'])
def get_current_aqi():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400
    data = aqi_fetcher.fetch_aqi_data(city)
    if "error" not in data:
        return jsonify(data)
    return jsonify(data), 500

@app.route('/store_aqi_data', methods=['POST'])
def store_aqi_data():
    data = request.json
    city = data.get('city')
    aqi = data.get('aqi')
    components = data.get('components', {})
    
    if not city or not aqi:
        return jsonify({"error": "City and AQI are required fields"}), 400
        
    database.save_aqi_reading(city, aqi, components)
    return jsonify({"success": True, "message": "AQI data stored successfully."})

@app.route('/predict_aqi', methods=['POST'])
def predict_aqi():
    """Predict AQI using Machine Learning Model."""
    data = request.json
    try:
        pm25 = data['pm25']
        pm10 = data['pm10']
        no2 = data['no2']
        co = data['co']
        so2 = data['so2']
        o3 = data['o3']
        temp = data['temperature']
        humidity = data['humidity']
        
        prediction = ml_predict_aqi(pm25, pm10, no2, co, so2, o3, temp, humidity)
        if prediction is None:
            return jsonify({"error": "Machine Learning module is not initialized or failed to load."}), 500
            
        return jsonify({"predicted_aqi": prediction})
    except KeyError as e:
        return jsonify({"error": f"Missing required parameter for prediction: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_historical_aqi', methods=['GET'])
def get_historical_aqi():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400
    trends = database.get_aqi_trends(city)
    return jsonify({"city": city, "history": trends})

@app.route('/chat', methods=['POST'])
def chat_proxy():
    """Secure Proxy for Gemini API to prevent key leaks."""
    user_data = request.json
    user_message = user_data.get('message', '')
    context = user_data.get('context', {})
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return jsonify({"error": "Gemini API Key missing on server environment."}), 500

    # Model attempts
    models = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-pro'
    ]

    system_context = "You are an expert AI Health Assistant. Concise answers (3 sentences). "
    if context.get('city'):
        system_context += f"City: {context['city']}, AQI: {context['aqi']} ({context.get('status', 'Unknown')}). Advice based on this."
    else:
        system_context += "Give general air quality health advice."

    full_prompt = f"{system_context}\n\nUser Question: {user_message}"
    
    last_error = "None"
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            }
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if response.status_code == 200 and 'candidates' in data:
                return jsonify({
                    "response": data['candidates'][0]['content']['parts'][0]['text'],
                    "model_used": model
                })
            else:
                last_error = data.get('error', {}).get('message', 'Unknown Error')
                print(f"[ChatProxy] Model {model} failed: {last_error}")
        except Exception as e:
            last_error = str(e)
            print(f"[ChatProxy] Fetch error for {model}: {e}")

    return jsonify({"error": "All AI models failed to respond.", "details": last_error}), 500

if __name__ == "__main__":
    print("Backend API server starting on port 5000...")
    app.run(port=5000, debug=True, use_reloader=False)
