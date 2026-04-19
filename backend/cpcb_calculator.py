def calculate_indian_aqi(components):
    """
    Calculates the Indian National Air Quality Index (NAQI) based on CPCB standards.
    Ref: strictly adheres to user-provided breakpoints.
    """
    def get_indian_sub_index(cp, breakpoints):
        for clo, chi, ilo, ihi in breakpoints:
            if clo <= cp <= chi:
                return ((ihi - ilo) / (chi - clo)) * (cp - clo) + ilo
        if breakpoints:
            _, chi, _, ihi = breakpoints[-1]
            if cp > chi: return ihi
        return 0

    # 1. Prepare concentrations
    pm25 = int(round(components.get('pm2_5', 0)))
    pm10 = int(round(components.get('pm10', 0)))
    co_mg = components.get('co', 0) / 1000.0  # Convert CO to mg/m³
    no2 = components.get('no2', 0)
    so2 = components.get('so2', 0)
    o3 = components.get('o3', 0)
    nh3 = components.get('nh3', 0)

    # 2. Define Breakpoints
    pm25_bp = [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200), (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)]
    pm10_bp = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200), (251, 350, 201, 300), (351, 430, 301, 400), (431, 600, 401, 500)]
    no2_bp = [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200), (181, 280, 201, 300), (281, 400, 301, 400), (401, 1000, 401, 500)]
    so2_bp = [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200), (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 10000, 401, 500)]
    co_bp = [(0, 1.0, 0, 50), (1.1, 2.0, 51, 100), (2.1, 10, 101, 200), (11, 17, 201, 300), (18, 34, 301, 400), (35, 100, 401, 500)]
    o3_bp = [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200), (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)]
    nh3_bp = [(0, 200, 0, 50), (201, 400, 51, 100), (401, 800, 101, 200), (801, 1200, 201, 300), (1201, 1800, 301, 400), (1801, 5000, 401, 500)]

    # 3. Calculate sub-indices
    indices = {}
    if pm25 > 0: indices['PM2.5'] = get_indian_sub_index(pm25, pm25_bp)
    if pm10 > 0: indices['PM10'] = get_indian_sub_index(pm10, pm10_bp)
    if no2 > 0: indices['NO2'] = get_indian_sub_index(no2, no2_bp)
    if so2 > 0: indices['SO2'] = get_indian_sub_index(so2, so2_bp)
    if o3 > 0: indices['O3'] = get_indian_sub_index(o3, o3_bp)
    if co_mg > 0: indices['CO'] = get_indian_sub_index(co_mg, co_bp)
    if nh3 > 0: indices['NH3'] = get_indian_sub_index(nh3, nh3_bp)
    
    if not indices:
        return {"aqi": 0, "level": 1, "category": "Good", "dominant_pollutant": "None", "health_message": "Minimal impact"}

    dominant_pollutant = max(indices, key=indices.get)
    final_aqi = int(round(indices[dominant_pollutant]))
    
    # 4. Map Categories and Health Messages
    if final_aqi <= 50:
        level, category = 1, "Good"
        health_message = "Minimal impact. Enjoy the outdoors!"
    elif final_aqi <= 100:
        level, category = 2, "Satisfactory"
        health_message = "Minor breathing discomfort to sensitive people."
    elif final_aqi <= 200:
        level, category = 3, "Moderate"
        health_message = "Breathing discomfort to people with lung, asthma and heart diseases."
    elif final_aqi <= 300:
        level, category = 4, "Poor"
        health_message = "Breathing discomfort to most people on prolonged exposure."
    elif final_aqi <= 400:
        level, category = 5, "Very Poor"
        health_message = "Respiratory illness on prolonged exposure."
    else:
        level, category = 6, "Severe"
        health_message = "Affects healthy people and seriously impacts those with existing diseases."
    
    return {
        "aqi": final_aqi,
        "level": level,
        "category": category,
        "dominant_pollutant": dominant_pollutant,
        "health_message": health_message,
        "sub_indices": indices
    }
