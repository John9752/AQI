from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import threading
import time
import os
import sys
import requests
import pandas as pd
import math
import hashlib
import random
from datetime import datetime
from pathlib import Path
from google import genai

# Load environment variables
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
                                database.save_aqi_reading(city_data['city'], city_data['aqi'], city_data['components'])

                        if city in checked_cities:
                            city_data = checked_cities[city]
                            simulated_aqi = city_data['aqi']
                            aqi_level = city_data['level']
                            
                            mapping = AQI_MAPPING.get(aqi_level, AQI_MAPPING[5])
                            # Send hourly update regardless of threshold (as per user request "once an hour")
                            email_service.send_aqi_alert(
                                email, city, simulated_aqi, 
                                mapping['name'], mapping['rec']
                            )
                    except Exception as e:
                        print(f"[Monitor ERROR] {e}")
            else:
                print("[Monitor] No active subscribers found.")
        except Exception as e:
            print(f"[Monitor Global Error] {e}")
        time.sleep(3600) # Hourly interval as requested

if not any(t.name == "AQIMonitor" for t in threading.enumerate()):
    monitor_thread = threading.Thread(target=monitor_aqi_background, name="AQIMonitor", daemon=True)
    monitor_thread.start()

# ==========================================
# API ENDPOINTS
# ==========================================
@app.route('/get_aqi', methods=['GET'])
def get_aqi_legacy():
    city = request.args.get('city')
    if not city: return jsonify({"error": "City parameter is required"}), 400
    data = aqi_fetcher.fetch_aqi_data(city)
    if "error" not in data:
        database.save_aqi_reading(data['city'], data['aqi'], data['components'])
        return jsonify(data)
    return jsonify(data), 500

@app.route('/get_aqi_coords', methods=['GET'])
def get_aqi_coords_legacy():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon: return jsonify({"error": "Latitude and longitude are required"}), 400
    data = aqi_fetcher.fetch_aqi_by_coords(lat, lon)
    if "error" not in data:
        db_city = data.get('city_for_db', data.get('city', 'Unknown'))
        database.save_aqi_reading(db_city, data['aqi'], data['components'])
        return jsonify(data)
    return jsonify(data), 500

@app.route('/aqi_trends', methods=['GET'])
def aqi_trends_legacy():
    city = request.args.get('city', '').lower().strip()
    if not city: return jsonify({"error": "City parameter is required"}), 400
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
    email, city = data.get('email'), data.get('city')
    threshold = data.get('threshold', 101)
    if not email or not city: return jsonify({"success": False, "message": "Email and City are required"}), 400
    if database.add_subscription(email, city, threshold):
        # Send immediate current AQI email
        try:
            city_data = aqi_fetcher.fetch_aqi_data(city)
            if "error" not in city_data:
                email_service.send_current_aqi_email(email, city, city_data)
        except Exception as e:
            print(f"Failed to send immediate alert: {e}")
            
        return jsonify({"success": True, "message": "Successfully subscribed to hourly alerts"})
    return jsonify({"success": False, "message": "Subscription failed"}), 500

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    email = request.args.get('email') or (request.json.get('email') if request.is_json else None)
    if not email: return jsonify({"success": False, "message": "Email is required"}), 400
    
    if database.delete_subscription(email):
        if request.method == 'GET':
            return "<h1>Successfully Unsubscribed</h1><p>You will no longer receive hourly AQI alerts.</p>"
        return jsonify({"success": True, "message": "Successfully unsubscribed from alerts"})
    return jsonify({"success": False, "message": "Unsubscribe failed"}), 500

@app.route('/get_user_preferences', methods=['GET'])
def get_user_preferences():
    email = request.args.get('email')
    if not email: return jsonify({"error": "Email is required"}), 400
    subs = database.get_subscriptions()
    for row in subs:
        if row[0] == email: return jsonify({"city": row[1], "threshold": row[2]})
    return jsonify({"city": "Visakhapatnam", "threshold": 101})

@app.route('/get_current_aqi', methods=['GET'])
def get_current_aqi():
    city = request.args.get('city')
    if not city: return jsonify({"error": "City is required"}), 400
    data = aqi_fetcher.fetch_aqi_data(city)
    return jsonify(data), (200 if "error" not in data else 500)

@app.route('/predict_aqi', methods=['POST'])
def predict_aqi():
    if ml_predict_aqi is None: return jsonify({"error": "ML module not found"}), 500
    data = request.json
    try:
        result = ml_predict_aqi(
            data['pm25'], data['pm10'], data['no2'], data['co'], 
            data['so2'], data['o3'], data['temperature'], data['humidity']
        )
        if result is not None:
            # Load accuracy metadata
            accuracy = 0
            try:
                metadata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'model', 'metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        meta = json.load(f)
                        accuracy = meta.get('r2_score', 0) * 100
            except Exception: pass
            
            return jsonify({
                "predicted_aqi": result,
                "accuracy": round(accuracy, 2)
            })
        return jsonify({"error": "Prediction failed"}), 500
    except Exception as e: return jsonify({"error": str(e)}), 400

@app.route('/get_historical_aqi', methods=['GET'])
def get_historical_aqi():
    city = request.args.get('city')
    if not city: return jsonify({"error": "City is required"}), 400
    return jsonify({"city": city, "history": database.get_aqi_trends(city)})

# ==========================================
# VIZAG FORECAST DATA & LOGIC
# ==========================================
VIZAG_AREAS = [
    'Visakhapatnam', 'Gajuwaka', 'MVP Colony', 'Madhurawada', 'Pendurthi',
    'Rushikonda', 'Asilmetta', 'Dwaraka Nagar', 'NAD X Road',
    'Seethammadhara', 'Siripuram', 'Bheemili', 'Anakapalle', 'Simhachalam',
    'Kancharapalem', 'Akkayyapalem', 'Maharanipeta', 'Jagadamba Centre',
    'Lawsons Bay Colony', 'Kirlampudi Layout', 'Waltair', 'Daba Gardens',
    'Allipuram', 'Ram Nagar', 'Pedagantyada', 'Gopalapatnam',
    'Kommadi', 'Yendada', 'Thatichetlapalem', 'Sagar Nagar',
    'Chinnamushidiwada', 'Gnanapuram', 'Peda Waltair', 'CBM Compound',
    'Isukathota', 'PM Palem', 'Hanumanthawaka', 'Kurupam Market',
    'Seethammapeta', 'Dondaparthy', 'Murali Nagar', 'HB Colony',
    'Resapuvanipalem', 'Thotagaruvu Peta', 'Nakkavanipalem',
    'Chinna Waltair', 'Old Town', 'One Town', 'Poorna Market',
    'Chengal Rao Peta', 'Dabagardens', 'MVP Double Road', 'Steel Plant',
    'Kurmannapalem', 'Gidijala', 'Adavivaram', 'Jodugullapalem',
    'Aganampudi', 'Pudimadaka', 'Bhogapuram', 'Parawada',
    'Sabbavaram', 'Chodavaram', 'Yelamanchili', 'Narsipatnam',
    'Payakaraopeta', 'Padmanabham', 'Anandapuram', 'Kothavalasa'
]

VIZAG_DEFAULTS = {
    'Visakhapatnam': {'mean': 53, 'std': 20, 'drift': -0.9},
    'Gajuwaka':      {'mean': 53, 'std': 20, 'drift': -0.9},
    'MVP Colony':    {'mean': 60, 'std': 18, 'drift': -0.5},
    'Madhurawada':   {'mean': 48, 'std': 15, 'drift': -0.3},
    'Pendurthi':     {'mean': 72, 'std': 22, 'drift': 0.8},
    'Rushikonda':    {'mean': 38, 'std': 12, 'drift': -0.6},
    'Asilmetta':     {'mean': 78, 'std': 24, 'drift': 1.0},
    'Dwaraka Nagar': {'mean': 82, 'std': 25, 'drift': 1.2},
    'NAD X Road':    {'mean': 90, 'std': 28, 'drift': 1.5},
    'Seethammadhara':{'mean': 58, 'std': 16, 'drift': -0.2},
    'Siripuram':     {'mean': 65, 'std': 18, 'drift': 0.3},
    'Bheemili':      {'mean': 35, 'std': 10, 'drift': -0.8},
    'Anakapalle':    {'mean': 88, 'std': 26, 'drift': 1.3},
    'Simhachalam':   {'mean': 55, 'std': 17, 'drift': -0.4},
    'Steel Plant':   {'mean': 95, 'std': 30, 'drift': 1.8},
    'Parawada':      {'mean': 85, 'std': 25, 'drift': 1.4},
}

def _get_vizag_stats(area):
    csv_path = BASE_DIR / 'dataset' / 'ap_historical.csv'
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        city_df = df[df['city'] == area]
        if not city_df.empty: return {'mean': float(city_df['AQI'].mean()), 'std': float(city_df['AQI'].std())}
    if area in VIZAG_DEFAULTS: return {'mean': VIZAG_DEFAULTS[area]['mean'], 'std': VIZAG_DEFAULTS[area]['std']}
    h = int(hashlib.md5(area.encode()).hexdigest(), 16)
    return {'mean': max(25, 53 + (h % 60) - 20), 'std': max(8, 15 + (h % 15))}

@app.route('/forecast_areas', methods=['GET'])
def forecast_areas(): return jsonify({"areas": VIZAG_AREAS})

@app.route('/vizag_10yr_forecast', methods=['GET'])
def vizag_10yr_forecast():
    area = request.args.get('area', 'Visakhapatnam')
    years = [str(y) for y in range(2026, 2037)]
    s = _get_vizag_stats(area)
    base, drift = s['mean'], (VIZAG_DEFAULTS.get(area, {}).get('drift', (s['mean'] - 60) * 0.02))
    random.seed(f"forecast_{area}")
    data, curr = [], base
    for _ in range(len(years)):
        val = curr + random.uniform(-0.08, 0.08) * curr
        data.append(int(round(max(0, val))))
        curr += drift
    return jsonify({"years": years, "area": area, "forecast": data, "baseline_mean": round(base, 1), "baseline_std": round(s['std'], 1)})

@app.route('/vizag_date_prediction', methods=['GET'])
def vizag_date_prediction():
    area, d_str = request.args.get('area'), request.args.get('date')
    if not area or not d_str: return jsonify({"error": "Missing params"}), 400
    try: t_date = datetime.strptime(d_str, '%Y-%m-%d')
    except: return jsonify({"error": "Invalid date"}), 400
    s = _get_vizag_stats(area)
    drift = VIZAG_DEFAULTS.get(area, {}).get('drift', (s['mean'] - 60) * 0.02)
    base_aqi = s['mean'] + (drift * max(0, t_date.year - 2026))
    random.seed(f"{area}_{d_str}")
    seasonal = 1.15 if t_date.month in [11, 12, 1, 2] else (0.85 if t_date.month in [6, 7, 8, 9] else 1.0)
    final_aqi = int(round(max(0, base_aqi * seasonal + random.gauss(0, s['std'] * 0.3))))
    cat = 'Good' if final_aqi <= 50 else ('Satisfactory' if final_aqi <= 100 else ('Moderate' if final_aqi <= 200 else ('Poor' if final_aqi <= 300 else ('Very Poor' if final_aqi <= 400 else 'Severe'))))
    return jsonify({"area": area, "date": d_str, "predicted_aqi": final_aqi, "category": cat})

# ==========================================
# CHAT PROXY & PAGE ROUTES
# ==========================================
@app.route('/chat', methods=['POST', 'GET'])
def chat_proxy():
    if request.method == 'GET': return jsonify({"status": "Online"})
    data = request.json
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return jsonify({"error": "API Key missing"}), 500
    
    user_query = data.get('message', '')
    system_prompt = (
        "You are the 'AQInsight Pro Health Assistant', an expert in air quality and respiratory health. "
        "Provide clear, actionable medical and practical precautions based on the user's AQI context. "
        "Keep responses professional, concise, and focused on safety."
    )
    
    # Try multiple models in case of 404/Not Found or versioning issues
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro', 'gemini-1.0-pro']
    last_error = ""

    try:
        # Force stable v1 API version
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        
        # AUTO-DETECT WORKING MODELS
        model_to_use = 'gemini-1.5-flash' # Standard fallback
        try:
            print(f"[AUTO-DETECT] Scanning for available models...")
            # Fetch all models that support generating content
            available_models = []
            for m in client.models.list():
                if 'generateContent' in m.supported_methods:
                    available_models.append(m.name)
            
            print(f"[AUTO-DETECT] Found {len(available_models)} models: {available_models}")
            
            if available_models:
                # Try to pick our preferred ones first, otherwise take the first available
                preferred = ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.0-pro']
                found_preferred = False
                for p in preferred:
                    if p in available_models:
                        model_to_use = p
                        found_preferred = True
                        break
                if not found_preferred:
                    model_to_use = available_models[0]
                
                print(f"[AUTO-DETECT] Selected model to use: {model_to_use}")
            else:
                print("[AUTO-DETECT] WARNING: No generative models found for this key!")
        except Exception as list_err:
            print(f"[AUTO-DETECT] Could not list models: {str(list_err)}")
        
        # Execute the chat with the selected (or fallback) model
        try:
            response = client.models.generate_content(
                model=model_to_use, 
                contents=f"{system_prompt}\n\nUser Question: {user_query}"
            )
            return jsonify({"response": response.text})
        except Exception as gen_err:
            print(f"[ERROR] Generation failed for {model_to_use}: {str(gen_err)}")
            return jsonify({"error": f"AI Assistant unavailable. {str(gen_err)}. Please verify your Gemini API key in AI Studio."}), 503
            
    except Exception as e:
        error_msg = str(e)
        print(f"[Chat Global Error] {error_msg}")
        return jsonify({"error": f"AI Assistant initialization failed. {error_msg}. Please try again."}), 503

@app.route('/')
def index_root(): return render_template('login.html')

@app.route('/index.html')
def index_page(): return render_template('index.html')

@app.route('/dashboard.html')
def dashboard_page(): return render_template('dashboard.html')

@app.route('/login.html')
def login_page(): return render_template('login.html')

@app.route('/signup.html')
def signup_page(): return render_template('signup.html')

@app.route('/profile.html')
def profile_page(): return render_template('profile.html')

@app.route('/health-advice.html')
def health_advice_page(): return render_template('health-advice.html')

@app.route('/<path:path>')
def serve_any(path):
    if (STATIC_DIR / path).exists(): return send_from_directory(str(STATIC_DIR), path)
    if path.endswith('.html') and (TEMPLATE_DIR / path).exists(): return render_template(path)
    return "Not Found", 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    is_prod = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') == 'true'
    app.run(host='0.0.0.0', port=port, debug=not is_prod)
