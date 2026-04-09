import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# ==========================================
# 0. HELPER: DATASET GENERATION (If missing)
# ==========================================
def generate_synthetic_data(file_path):
    """Generates a synthetic dataset for AQI training for demonstration."""
    print(f"Dataset not found. Generating synthetic data: {file_path}")
    np.random.seed(42)
    n_samples = 1000
    
    # Random pollution values
    pm25 = np.random.uniform(0, 300, n_samples)
    pm10 = pm25 * 1.2 + np.random.normal(0, 10, n_samples)
    no2 = np.random.uniform(0, 100, n_samples)
    co = np.random.uniform(0, 5, n_samples)
    so2 = np.random.uniform(0, 50, n_samples)
    o3 = np.random.uniform(0, 150, n_samples)
    temp = np.random.uniform(10, 40, n_samples)
    humidity = np.random.uniform(20, 90, n_samples)
    
    # Complex linear relationship for AQI simulation
    aqi = (pm25 * 0.5) + (pm10 * 0.2) + (no2 * 0.3) + (co * 10) + (o3 * 0.1) + np.random.normal(0, 5, n_samples)
    
    df = pd.DataFrame({
        'PM2.5': pm25, 'PM10': pm10, 'NO2': no2, 'CO': co, 
        'SO2': so2, 'O3': o3, 'Temperature': temp, 'Humidity': humidity, 'AQI': aqi
    })
    df.to_csv(file_path, index=False)
    print("Synthetic data generated successfully.\n")

# ==========================================
# 1. LOAD DATASET
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'dataset', 'aqi_dataset.csv')
MODEL_NAME = os.path.join(BASE_DIR, 'model', 'aqi_model.pkl')

# Load model globally to avoid reloading on every request
trained_model = None
if os.path.exists(MODEL_NAME):
    try:
        trained_model = joblib.load(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model: {e}")


if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        generate_synthetic_data(DATA_FILE)

    print("--- Loading Dataset ---")
    df = pd.read_csv(DATA_FILE)
    print(f"Dataset Shape: {df.shape}")
    print(df.head())

    # ==========================================
    # 2. DATA PREPROCESSING
    # ==========================================
    print("\n--- Preprocessing ---")
    # Check for null values
    if df.isnull().values.any():
        print("Missing values detected. Cleaning...")
        df = df.dropna()

    # Separate Input Features (X) and Target Variable (y)
    X = df[['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity']]
    y = df['AQI']

    # ==========================================
    # 3. SPLIT THE DATASET
    # ==========================================
    # Split into 80% Training and 20% Testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print("Data split into training and testing sets (80/20).")

    # ==========================================
    # 4. TRAIN THE MODEL
    # ==========================================
    print("\n--- Training Model ---")
    # Initialize Random Forest Regressor
    # n_estimators is the number of trees in the forest
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("Random Forest Regressor trained successfully.")

    # ==========================================
    # 5. EVALUATE THE MODEL
    # ==========================================
    print("\n--- Evaluating Model ---")
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"R² Score: {r2:.4f}")

    # ==========================================
    # 6. SAVE THE MODEL
    # ==========================================
    if not os.path.exists(os.path.dirname(MODEL_NAME)):
        os.makedirs(os.path.dirname(MODEL_NAME))
        
    joblib.dump(model, MODEL_NAME)
    print(f"\nModel saved locally as: {MODEL_NAME}")
    
    # Update the global reference for immediate use in this process if needed
    trained_model = model

# ==========================================
# 7. PREDICTION FUNCTION
# ==========================================
def predict_aqi(pm25, pm10, no2, co, so2, o3, temp, humidity):
    """
    Predicts AQI based on input pollution and weather values.
    """
    global trained_model
    
    # Lazy load if not yet loaded
    if trained_model is None:
        print(f"Loading model from {MODEL_NAME}...")
        if os.path.exists(MODEL_NAME):
            try:
                trained_model = joblib.load(MODEL_NAME)
                print("Model loaded successfully.")
            except Exception as e:
                print(f"Error loading model: {e}")
                return None
        else:
            print(f"Model file NOT found at {MODEL_NAME}")
            return None
            
    # Prepare input data in the same format as X
    try:
        input_df = pd.DataFrame([[pm25, pm10, no2, co, so2, o3, temp, humidity]], 
                                columns=['PM2.5', 'PM10', 'NO2', 'CO', 'SO2', 'O3', 'Temperature', 'Humidity'])
        
        prediction = trained_model.predict(input_df)[0]
        return float(prediction)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

# Test the prediction function
if __name__ == "__main__":
    print("\n--- Testing Prediction Function ---")
    sample_prediction = predict_aqi(120, 140, 45, 1.2, 10, 80, 25, 60)
    print(f"Predicted AQI for sample input: {sample_prediction:.2f}")
