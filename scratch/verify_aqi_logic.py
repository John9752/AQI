import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.cpcb_calculator import calculate_indian_aqi

def test_scenarios():
    scenarios = [
        {"pm2_5": 30, "pm10": 50, "no2": 40, "co": 1000, "label": "Good Level"},
        {"pm2_5": 60, "pm10": 100, "no2": 80, "co": 2000, "label": "Satisfactory Level"},
        {"pm2_5": 100, "pm10": 260, "label": "Poor Level (PM10 dominant)"},
        {"pm2_5": 250, "label": "Very Poor Level"},
        {"pm2_5": 300, "label": "Severe Level"},
    ]

    print(f"{'Label':<30} | {'AQI':<5} | {'Category':<15} | {'Dominant'}")
    print("-" * 65)
    for sc in scenarios:
        res = calculate_indian_aqi(sc)
        print(f"{sc['label']:<30} | {res['aqi']:<5} | {res['category']:<15} | {res['dominant_pollutant']}")

if __name__ == "__main__":
    test_scenarios()
