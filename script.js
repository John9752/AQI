// ==========================================
// FRONTEND CONFIGURATION (Pro Version)
// ==========================================
// Use the deployed Flask backend if the frontend is loaded from another origin
// such as Live Server on port 5500.
const BACKEND_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000'];
const API_BASE_URL = BACKEND_ORIGINS.includes(window.location.origin)
    ? ''
    : 'http://127.0.0.1:5000';

const cityInput = document.getElementById('cityInput');
const searchBtn = document.getElementById('searchBtn');
const cityNameDisplay = document.getElementById('cityNameDisplay');
const aqiValueDisplay = document.getElementById('aqiValue');
const aqiStatusDisplay = document.getElementById('aqiStatus');
const healthRecDisplay = document.getElementById('healthRecommendation');
const aqiCircle = document.getElementById('aqiCircle');
const alertContainer = document.getElementById('alertContainer');
const subEmailInput = document.getElementById('subEmail');
const subscribeBtn = document.getElementById('subscribeBtn');

// AQI Visual Mapping (Consistent with Backend)
const AQI_MAPPING = {
    1: { label: "Good", colorClass: "aqi-1", textClass: "text-1", recommendation: "Air quality is satisfactory. Ideal for outdoor activities." },
    2: { label: "Fair", colorClass: "aqi-2", textClass: "text-2", recommendation: "Sensitive people should consider limiting prolonged outdoor exertion." },
    3: { label: "Moderate", colorClass: "aqi-3", textClass: "text-3", recommendation: "Sensitive groups may experience health effects. Limit outdoor exertion." },
    4: { label: "Poor", colorClass: "aqi-4", textClass: "text-4", recommendation: "Health alert! Avoid outdoor activities and wear masks." },
    5: { label: "Very Poor", colorClass: "aqi-5", textClass: "text-5", recommendation: "Health warnings of emergency conditions. Stay indoors." }
};

if (searchBtn) {
    searchBtn.addEventListener('click', () => {
        const city = cityInput.value.trim();
        if (city) {
            fetchDashboardData(city);
        }
    });

    cityInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const city = cityInput.value.trim();
            if (city) {
                fetchDashboardData(city);
            }
        }
    });
}

if (subscribeBtn) {
    subscribeBtn.addEventListener('click', handleSubscription);
}

// Map Click Listener (Coordinates from charts.js)
document.addEventListener('mapLocationSelected', (e) => {
    const { lat, lon } = e.detail;
    loadDataByCoords(lat, lon);
});

async function fetchDashboardData(city) {
    try {
        // Step 1: Fetch current AQI from our Backend
        const response = await fetch(`${API_BASE_URL}/get_aqi?city=${city}`);
        const data = await response.json();

        if (data.error) {
            showAlert(data.error);
            return;
        }

        // Update UI
        updateUI(data);

        document.dispatchEvent(new CustomEvent('renderPollutants', { detail: data.components }));
        document.dispatchEvent(new CustomEvent('renderMap', { detail: { coordinates: data.coordinates, city: data.city, level: data.level } }));
        
        // Step 1.5: Trigger AI Prediction
        const componentsForPredict = {
            pm25: data.components.pm2_5,
            pm10: data.components.pm10,
            no2: data.components.no2,
            co: data.components.co,
            so2: data.components.so2,
            o3: data.components.o3,
            temperature: data.components.temperature || 25,
            humidity: data.components.humidity || 50
        };
        fetchPrediction(componentsForPredict);
        
        // Step 2: Fetch Trend data
        fetchTrendData(city);

    } catch (error) {
        console.error("Fetch Error:", error);
        showAlert("Check if your Backend (app.py) is running on port 5000.");
    }
}

async function loadDataByCoords(lat, lon) {
    try {
        const response = await fetch(`${API_BASE_URL}/get_aqi_coords?lat=${lat}&lon=${lon}`);
        const data = await response.json();

        if (data.error) {
            showAlert(data.error);
            return;
        }

        // Update UI with coordinates data
        updateUI(data);

        document.dispatchEvent(new CustomEvent('renderPollutants', { detail: data.components }));
        document.dispatchEvent(new CustomEvent('renderMap', { detail: { coordinates: data.coordinates, city: data.city, level: data.level } }));
        // Step 1.5: Trigger AI Prediction
        const componentsForPredict = {
            pm25: data.components.pm2_5,
            pm10: data.components.pm10,
            no2: data.components.no2,
            co: data.components.co,
            so2: data.components.so2,
            o3: data.components.o3,
            temperature: data.components.temperature || 25,
            humidity: data.components.humidity || 50
        };
        fetchPrediction(componentsForPredict);
        
        // Fetch Trends for the area (if possible, current database stores by city name)
        const cityOnly = data.city.split(',')[0].trim();
        fetchTrendData(cityOnly);

    } catch (error) {
        console.error("Coords Fetch Error:", error);
    }
}

async function fetchTrendData(city) {
    try {
        const response = await fetch(`${API_BASE_URL}/aqi_trends?city=${city}`);
        const trends = await response.json();
        
        if (trends && trends.length > 0) {
            document.dispatchEvent(new CustomEvent('renderTrends', { detail: trends }));
        }
    } catch (error) {
        console.warn("Could not fetch trends:", error);
    }
}

function updateUI(data) {
    const config = AQI_MAPPING[data.level];
    
    cityNameDisplay.textContent = data.city;
    aqiValueDisplay.textContent = data.aqi;
    aqiStatusDisplay.textContent = config.label;
    healthRecDisplay.textContent = config.recommendation;

    // Reset styles
    aqiCircle.className = 'aqi-circle';
    aqiStatusDisplay.className = 'aqi-status';
    
    // Apply dynamic classes
    aqiCircle.classList.add(config.colorClass);
    aqiStatusDisplay.classList.add(config.textClass);

    // Visual Alert logic
    alertContainer.innerHTML = '';
    if (data.level >= 4) {
        alertContainer.innerHTML = `
            <div class="alert">
                <span><strong>High Pollution Alert:</strong> ${config.recommendation}</span>
            </div>
        `;
    }
}

async function handleSubscription() {
    const email = subEmailInput.value.trim();
    const city = cityNameDisplay.textContent.split(',')[0].trim();

    if (!email || city === "Detecting...") {
        showAlert("Please enter a valid email and search for a city first.");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/subscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, city })
        });
        const result = await response.json();
        
        if (result.success) {
            alert("Subscription successful! You will receive alerts for " + city);
            subEmailInput.value = '';
        } else {
            showAlert(result.message);
        }
    } catch (error) {
        showAlert("Could not connect to subscription service.");
    }
}

function showAlert(message) {
    alertContainer.innerHTML = `
        <div class="alert danger">
            <span><strong>Warning:</strong> ${message}</span>
        </div>
    `;
    setTimeout(() => { alertContainer.innerHTML = ''; }, 5000);
}

async function fetchPrediction(components) {
    const aiPredictionDisplay = document.getElementById('aiPredictionValue'); // dashboard.html
    const tomorrowAqiDisplay = document.getElementById('tomorrowAqi'); // index.html
    const trendTextDisplay = document.getElementById('trendText'); // index.html
    
    if (aiPredictionDisplay) aiPredictionDisplay.textContent = "Calculating...";
    if (tomorrowAqiDisplay) tomorrowAqiDisplay.textContent = "Calculating...";

    try {
        const response = await fetch(`${API_BASE_URL}/predict_aqi`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(components)
        });
        const result = await response.json();
        
        if (result.predicted_aqi !== undefined) {
            const val = Math.round(result.predicted_aqi);
            if (aiPredictionDisplay) aiPredictionDisplay.textContent = `${val} AQI`;
            if (tomorrowAqiDisplay) tomorrowAqiDisplay.textContent = `${val} AQI`;
            if (trendTextDisplay) trendTextDisplay.textContent = "Forecast successfully generated from live data.";
        } else {
            if (aiPredictionDisplay) aiPredictionDisplay.textContent = "Unavailable";
            if (tomorrowAqiDisplay) tomorrowAqiDisplay.textContent = "Unavailable";
            console.warn("Prediction error:", result.error);
        }
    } catch (error) {
        if (aiPredictionDisplay) aiPredictionDisplay.textContent = "Error";
        if (tomorrowAqiDisplay) tomorrowAqiDisplay.textContent = "Error";
        console.error("Prediction fetch error:", error);
    }
}

// Initial Load
window.addEventListener('load', () => {
    if (cityInput) {
        cityInput.value = 'New York';
        fetchDashboardData('New York');
    }
});
