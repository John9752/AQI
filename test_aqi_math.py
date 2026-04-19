from backend.aqi_fetcher import calculate_usaqi

def test_aqi():
    test_cases = [
        # PM2.5 = 12.0 -> AQI 50
        {"components": {"pm2_5": 12.0}, "expected_aqi": 50, "expected_level": 1},
        # PM2.5 = 35.4 -> AQI 100
        {"components": {"pm2_5": 35.4}, "expected_aqi": 100, "expected_level": 2},
        # PM2.5 = 55.4 -> AQI 150
        {"components": {"pm2_5": 55.4}, "expected_aqi": 150, "expected_level": 3},
        # PM10 = 154 -> AQI 100
        {"components": {"pm10": 154}, "expected_aqi": 100, "expected_level": 2},
        # Combined case: PM2.5=35.4 (100) and PM10=254 (150) -> should be 150
        {"components": {"pm2_5": 35.4, "pm10": 254}, "expected_aqi": 150, "expected_level": 3},
    ]

    print("--- Testing EPA AQI Calculation ---")
    for i, tc in enumerate(test_cases):
        aqi, level = calculate_usaqi(tc['components'])
        print(f"Test {i+1}: Input {tc['components']}")
        print(f"  Result: AQI={aqi}, Level={level}")
        print(f"  Expected: AQI={tc['expected_aqi']}, Level={tc['expected_level']}")
        assert aqi == tc['expected_aqi'], f"AQI mismatch in test {i+1}"
        assert level == tc['expected_level'], f"Level mismatch in test {i+1}"
        print("  OK")

if __name__ == "__main__":
    test_aqi()
