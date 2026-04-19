import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from aqi_fetcher import calculate_indian_aqi

def test_indian_aqi():
    test_cases = [
        # PM2.5 = 30 -> AQI 50 (Good)
        {"components": {"pm2_5": 30}, "expected_aqi": 50, "expected_level": 1},
        # PM2.5 = 60 -> AQI 100 (Satisfactory)
        {"components": {"pm2_5": 60}, "expected_aqi": 100, "expected_level": 2},
        # PM2.5 = 90 -> AQI 200 (Moderate)
        {"components": {"pm2_5": 90}, "expected_aqi": 200, "expected_level": 3},
        # PM10 = 100 -> AQI 100 (Satisfactory)
        {"components": {"pm10": 100}, "expected_aqi": 100, "expected_level": 2},
        # CO = 2.0 mg/m3 -> AQI 100 (Satisfactory). OpenWeather uses ug/m3. 2.0 mg/m3 = 2000 ug/m3
        {"components": {"co": 2000}, "expected_aqi": 100, "expected_level": 2},
    ]

    print("--- Testing Indian National AQI Calculation (CPCB) ---")
    for i, tc in enumerate(test_cases):
        aqi, level = calculate_indian_aqi(tc['components'])
        print(f"Test {i+1}: Input {tc['components']}")
        print(f"  Result: AQI={aqi}, Level={level}")
        print(f"  Expected: AQI={tc['expected_aqi']}, Level={tc['expected_level']}")
        assert aqi == tc['expected_aqi'], f"AQI mismatch in test {i+1}"
        assert level == tc['expected_level'], f"Level mismatch in test {i+1}"
        print("  OK")

if __name__ == "__main__":
    test_indian_aqi()
