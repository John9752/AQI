import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import json
import joblib
import os

# ==========================================
# 1. LOAD APSET
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'dataset', 'ap_historical.csv')
MODEL_NAME = os.path.join(BASE_DIR, 'model', 'aqi_model.pkl')
SCALER_NAME = os.path.join(BASE_DIR, 'model', 'scaler.pkl')

# Load objects globally
trained_model = None
scaler = None

def load_resources():
    global trained_model, scaler
    if os.path.exists(MODEL_NAME):
        trained_model = joblib.load(MODEL_NAME)
    if os.path.exists(SCALER_NAME):
        scaler = joblib.load(SCALER_NAME)

if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        print(f"Error: dataset not found at {DATA_FILE}. Please run collect_ap_data.py first.")
        exit(1)

    print("--- Loading AP Historical Dataset ---")
    df = pd.read_csv(DATA_FILE)
    print(f"Dataset Shape: {df.shape}")
    
    # 2. PREPROCESSING
    print("\n--- Preprocessing ---")
    X = df[['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity']]
    y = df['AQI']

    # Standardize Features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    print("Data split into training and testing sets (80/20).")

    # ==========================================
    # 3. HYPERPARAMETER TUNING (Requirement #4)
    # ==========================================
    print("\n--- Tuning Model (Grid Search) ---")
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.1]
    }
    xgb = XGBRegressor(random_state=42, objective='reg:squarederror')
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=3, n_jobs=-1, scoring='r2')
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    print(f"Best Parameters: {grid_search.best_params_}")

    # ==========================================
    # 4. EVALUATION (Requirement #3)
    # ==========================================
    print("\n--- Evaluating Model ---")
    y_pred = best_model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Cross-Validation (Requirement #4)
    cv_scores = cross_val_score(best_model, X_scaled, y, cv=5)

    print(f"Mean Absolute Error (MAE): {mae:.2f}")
    print(f"R² Score: {r2:.4f}")
    print(f"CV Accuracy (Mean R²): {cv_scores.mean():.4f}")

    # ==========================================
    # 5. SAVE RESOURCES
    # ==========================================
    if not os.path.exists(os.path.dirname(MODEL_NAME)):
        os.makedirs(os.path.dirname(MODEL_NAME))
        
    joblib.dump(best_model, MODEL_NAME)
    joblib.dump(scaler, SCALER_NAME)
    
    # Save metadata for UI
    metadata = {
        "r2_score": float(r2),
        "mae": float(mae),
        "cv_accuracy": float(cv_scores.mean()),
        "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(os.path.join(os.path.dirname(MODEL_NAME), 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
        
    print(f"\nModel, Scaler & Metadata saved successfully.")

# ==========================================
# 6. PRODUCTION PREDICTION FUNCTION
# ==========================================
def predict_aqi(pm25, pm10, no2, co, so2, o3, temp, humidity):
    global trained_model, scaler
    
    if trained_model is None or scaler is None:
        load_resources()
        if trained_model is None or scaler is None:
            return None
            
    try:
        input_data = [[pm25, pm10, no2, co, so2, o3, temp, humidity]]
        input_scaled = scaler.transform(input_data)
        prediction = trained_model.predict(input_scaled)[0]
        return float(prediction)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None
