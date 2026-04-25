# Personal AQI Health Assistant - Project Details

The **Personal AQI Health Assistant** is a full-stack web application designed to help users monitor air quality index (AQI) in real-time, receive health advice based on various pollutants, and access predictive insights powered by machine learning.

## 🚀 Technology Stack

### Backend
- **Framework**: Python / Flask
- **Database**: SQLite (`aqi_assistant.db`)
- **Standards**: Indian CPCB (Central Pollution Control Board) AQI calculation logic.
- **External APIs**: 
  - OpenWeather (OWM) for weather/pollutant data.
  - WAQI/Google AQI (via `aqi_fetcher.py`).
  - Google Gemini API for AI-powered health assistant chat.
- **Mail**: Custom email service for alerts (`email_service.py`).

### Frontend
- **Design System**: Modern "Glass-morphism" aesthetic with vibrant colors and dark mode.
- **Languages**: HTML5, Vanilla CSS, and JavaScript.
- **Structure**: Templates located in `frontend-deploy` (optimized for Vercel) and `frontend/templates`.

### Machine Learning
- **Model**: Predictive model for AQI forecasting.
- **Files**: Located in `ml_model/` and `model/` (includes `aqi_model.pkl`).
- **Functionality**: Predicts future AQI levels based on current metrics.

## ✨ Key Features

1.  **Dynamic Dashboard**: Real-time AQI monitoring for multiple cities with colored status indicators (Good, Satisfactory, Moderate, Poor, Very Poor, Severe).
2.  **CPCB Integration**: Precise AQI calculation using Indian standards for pollutants like PM2.5, PM10, NO2, SO2, CO, O3, and NH3.
3.  **Predictive Forecasts**: ML-based predictions for tomorrow's AQI.
4.  **Health Advice Engine**: Personalized health recommendations based on specific pollutant concentrations.
5.  **User Profiles**: Manage personal settings and preferences.
6.  **Email Alerts**: Automated notifications for high pollution levels.
7.  **AI Assistant**: A chat interface powered by Gemini to answer health-related AQI questions.

## 🛠️ Recent Developments

- **Deployment Ready**: Configured for Render (Backend) and Vercel (Frontend).
- **Database Optimization**: Upgraded schema to include temperature and humidity for better data tracking.
- **Performance Fixes**: ML model now loads once at startup for faster response times.
- **Profile Page**: Added a dedicated `profile.html` for user management.

## 📁 Project Structure

```text
aqi/
├── backend/            # Flask API, Fetchers, Calculators, Email Service
├── frontend-deploy/    # Core dashboard and user management pages
├── ml_model/           # ML training scripts
├── dataset/            # Data used for model training
├── model/              # Serialized ML model files (.pkl)
├── aqi_assistant.db    # Primary application database
├── render.yaml         # Render deployment configuration
└── vercel.json         # Vercel deployment configuration
```
