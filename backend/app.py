from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import threading
import time
import os
import sys
import requests
from pathlib import Path

# Load environment variables
# Use Path for more robust path handling across environments
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# Setup paths
FRONTEND_DIR = BASE_DIR / 'frontend'
TEMPLATE_DIR = FRONTEND_DIR / 'templates'
STATIC_DIR = FRONTEND_DIR / 'static'

# Import local modules
sys.path.insert(0, str(BASE_DIR))
import backend.database as database
import backend.aqi_fetcher as aqi_fetcher
import backend.email_service as email_service

app = Flask(__name__, 
            template_folder=str(TEMPLATE_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path='/static')
CORS(app)

# Startup check for critical API keys
def check_environment():
    missing = []
    if not os.getenv("OPENWEATHER_API_KEY"):
        missing.append("OPENWEATHER_API_KEY")
    if not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    
    if missing:
        print(f"!!! WARNING: Missing environment variables: {', '.join(missing)} !!!")
        print("Please set these in your hosting provider's dashboard (Render/Vercel).")

check_environment()

try:
    from ml_model.train_model import predict_aqi as ml_predict_aqi
except ImportError:
    print("Warning: ML model module not found. AQI predictions may be unavailable.")
    ml_predict_aqi = None

# Initialize Database
database.init_db()

# CONFIGURATION mapping (CPCB Standards)
AQI_MAPPING = {
    1: {"name": "Good", "rec": "Air quality is ideal for outdoor activities. No health impacts expected."},
    2: {"name": "Satisfactory", "rec": "Minor breathing discomfort to sensitive people. May limit prolonged exertion."},
    3: {"name": "Moderate", "rec": "Breathing discomfort to the people with lungs, asthma and heart diseases."},
    4: {"name": "Poor", "rec": "Breathing discomfort to most people on prolonged exposure. Avoid outdoors."},
    5: {"name": "Very Poor", "rec": "Respiratory illness on prolonged exposure. Stay indoors, wear masks."},
    6: {"name": "Severe", "rec": "Health warnings of emergency conditions. Severe respiratory effects. Avoid all outdoor activities."}
}

# ==========================================
# BACKGROUND MONITORING LOGIC
# ==========================================
def monitor_aqi_background():
    # Wait a bit for server to fully start
    time.sleep(5)
    while True:
        try:
            print("[Monitor] Checking AQI for subscribers...")
            subs = database.get_subscriptions()
            checked_cities = {}

            if subs:
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
                            
                            print(f"[Monitor]   - {email}: Current AQI {simulated_aqi} (Threshold: {threshold})")
                            
                            if simulated_aqi >= threshold:
                                mapping = AQI_MAPPING.get(aqi_level, AQI_MAPPING[5])
                                email_service.send_aqi_alert(
                                    email, city, simulated_aqi, 
                                    mapping['name'], mapping['rec']
                                )
                    except Exception as e:
                        print(f"[Monitor] Error processing alert for {email}: {e}")
            else:
                print("[Monitor] No active subscribers found.")
        except Exception as e:
            print(f"[Monitor Global Error] {e}")

        # Wait for 30 minutes
        time.sleep(1800)

if not any(t.name == "AQIMonitor" for t in threading.enumerate()):
    monitor_thread = threading.Thread(target=monitor_aqi_background, name="AQIMonitor", daemon=True)
    monitor_thread.start()

# ==========================================
# API ENDPOINTS
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
        db_city = data.get('city_for_db', data.get('city', 'Unknown'))
        database.save_aqi_reading(db_city, data['aqi'], data['components'])
        return jsonify(data)
    return jsonify(data), 500

@app.route('/aqi_trends', methods=['GET'])
def aqi_trends_legacy():
    city = request.args.get('city', '').lower().strip()
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    
    trends = database.get_aqi_trends(city)
    
    if len(trends) == 0:
        geo = aqi_fetcher.fetch_aqi_data(city)
        if "error" not in geo:
            canonical_city = geo['city'].lower().strip()
            trends = database.get_aqi_trends(canonical_city)
    
    if len(trends) < 4:
        hist_trends = aqi_fetcher.fetch_historical_aqi(city)
        if isinstance(hist_trends, list) and len(hist_trends) > 0:
            db_dates = {t['date'] for t in trends}
            merged = [t for t in hist_trends if t['date'] not in db_dates]
            merged.extend(trends)
            merged.sort(key=lambda x: x['date'])
            return jsonify(merged)
            
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

@app.route('/get_user_preferences', methods=['GET'])
def get_user_preferences():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    subs = database.get_subscriptions()
    for row in subs:
        if row[0] == email:
            return jsonify({"city": row[1], "threshold": row[2]})
    return jsonify({"city": "Visakhapatnam", "threshold": 101})

@app.route('/get_current_aqi', methods=['GET'])
def get_current_aqi():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400
    data = aqi_fetcher.fetch_aqi_data(city)
    if "error" not in data:
        return jsonify(data)
    return jsonify(data), 500

@app.route('/predict_aqi', methods=['POST'])
def predict_aqi():
    if ml_predict_aqi is None:
        return jsonify({"error": "Machine Learning module is not available."}), 500
        
    data = request.json
    try:
        prediction = ml_predict_aqi(
            data['pm25'], data['pm10'], data['no2'], data['co'], 
            data['so2'], data['o3'], data['temperature'], data['humidity']
        )
        if prediction is None:
            return jsonify({"error": "ML Model failed to load or process data."}), 500
        return jsonify({"predicted_aqi": prediction})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ==========================================
# PAGE ROUTES
# ==========================================
@app.route('/')
def index_root():
    return render_template('login.html')

@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/dashboard.html')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/signup.html')
def signup_page():
    return render_template('signup.html')

@app.route('/profile.html')
def profile_page():
    return render_template('profile.html')

@app.route('/health-advice.html')
def health_advice_page():
    return render_template('health-advice.html')

@app.route('/unsubscribe', methods=['POST'])
def unsubscribe_api():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"success": False, "message": "Email required"}), 400
    if database.delete_subscription(email):
        return jsonify({"success": True, "message": "Unsubscribed successfully."})
    return jsonify({"success": False, "message": "Unsubscribe failed."}), 500

@app.route('/unsubscribe_confirm', methods=['GET'])
def unsubscribe_confirm():
    email = request.args.get('email')
    if not email: return "No email provided.", 400
    if database.delete_subscription(email):
        return render_template('unsubscribe_success.html', email=email)
    return "Error processing unsubscription.", 500

@app.route('/<path:path>')
def serve_any(path):
    # Try to find in static folder
    if (STATIC_DIR / path).exists():
        return send_from_directory(str(STATIC_DIR), path)
    # Try to find in templates (for .html links)
    if path.endswith('.html') and (TEMPLATE_DIR / path).exists():
        return render_template(path)
    return "Not Found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    # In production, debug should be False
    is_prod = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') == 'true'
    app.run(host='0.0.0.0', port=port, debug=not is_prod)
