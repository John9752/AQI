// Global instances to manage chart lifecycle
let pollutantsChart = null;
let trendChart = null;
let areaChart = null;
let mapInstance = null;

// ==========================================
// EVENT LISTENERS
// ==========================================

document.addEventListener('renderPollutants', (e) => {
    const components = e.detail;
    initPollutantsChart(components);
    // Area chart reuse current data for visual variance demonstration
    initAreaChart(components); 
});

document.addEventListener('renderTrends', (e) => {
    const trends = e.detail;
    initTrendChart(trends);
});

document.addEventListener('renderMap', (e) => {
    const { coordinates, city, level } = e.detail;
    initMap(coordinates, city, level);
});

// ==========================================
// CHART INITIALIZERS
// ==========================================

function initPollutantsChart(components) {
    const ctx = document.getElementById('pollutantsChart')?.getContext('2d');
    if (!ctx) return;

    if (pollutantsChart) {
        pollutantsChart.destroy();
    }

    const labels = ['PM2.5', 'PM10', 'CO', 'NO2', 'O3', 'SO2'];
    const dataValues = [
        components.pm2_5, 
        components.pm10, 
        components.co / 100, // Normalized for visual balance
        components.no2, 
        components.o3, 
        components.so2
    ];

    pollutantsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Concentration (μg/m³)',
                data: dataValues,
                backgroundColor: 'rgba(59, 130, 246, 0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: getCommonOptions('Pollutants Concentration')
    });
}

function initTrendChart(trends) {
    const ctx = document.getElementById('trendChart')?.getContext('2d');
    if (!ctx) return;

    if (trendChart) {
        trendChart.destroy();
    }

    const labels = trends.map(t => t.date);
    const dataValues = trends.map(t => t.aqi);

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Average AQI',
                data: dataValues,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#10b981'
            }]
        },
        options: getCommonOptions('Daily Trend')
    });
}

function initAreaChart(components) {
    const ctx = document.getElementById('areaChart')?.getContext('2d');
    if (!ctx) return;

    if (areaChart) {
        areaChart.destroy();
    }

    // Creating a mock daily variance for demo purposes using current data
    const mockHours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
    const baseAqi = components.aqi || 100;
    const mockData = mockHours.map(() => baseAqi + (Math.random() * 40 - 20));

    areaChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: mockHours,
            datasets: [{
                label: 'Hourly Variance',
                data: mockData,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                fill: true,
                tension: 0.5
            }]
        },
        options: getCommonOptions('Intraday Stability')
    });
}

function initMap(coords, cityName, level) {
    if (!coords) return;

    if (!mapInstance) {
        mapInstance = L.map('map').setView([coords.lat, coords.lon], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        }).addTo(mapInstance);

        // Add Click Explorer
        mapInstance.on('click', (e) => {
            const { lat, lng } = e.latlng;
            document.dispatchEvent(new CustomEvent('mapLocationSelected', { 
                detail: { lat, lon: lng } 
            }));
        });
    } else {
        mapInstance.setView([coords.lat, coords.lon], 13);
    }

    // Clear previous markers
    mapInstance.eachLayer((layer) => {
        if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
            mapInstance.removeLayer(layer);
        }
    });

    const colorMap = {
        1: '#10b981', // green
        2: '#fbbf24', // yellow
        3: '#f59e0b', // orange
        4: '#ef4444', // red
        5: '#8b5cf6'  // purple
    };
    const markerColor = colorMap[level] || '#3b82f6';

    L.circle([coords.lat, coords.lon], {
        radius: 8000,
        fillColor: markerColor,
        color: markerColor,
        weight: 0,
        opacity: 0,
        fillOpacity: 0.6,
        className: 'aqi-cloudy-circle'
    }).addTo(mapInstance)
        .bindPopup(`<b>${cityName}</b><br>AQI Index Level: ${level || 'Unknown'}`)
        .openPopup();
}

// ==========================================
// UTILITIES
// ==========================================

function getCommonOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                titleColor: '#fff',
                bodyColor: '#cbd5e1',
                padding: 12,
                cornerRadius: 8
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#cbd5e1', font: { size: 11 } }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#cbd5e1', font: { size: 11 } }
            }
        }
    };
}

// ==========================================
// DATA MAPPING & CONFIGURATION
// ==========================================
const AQI_MAPPING = {
    1: { label: 'Good', colorClass: 'good', textClass: 'text-good', recommendation: 'Air quality is satisfactory. Ideal for outdoor activities.' },
    2: { label: 'Moderate', colorClass: 'moderate', textClass: 'text-moderate', recommendation: 'Air quality is acceptable. Sensitive individuals should limit exertion.' },
    3: { label: 'Unhealthy for Sensitive Groups', colorClass: 'unhealthy-sensitive', textClass: 'text-warning', recommendation: 'Sensitive groups may experience health effects. Limit outdoor exertion.' },
    4: { label: 'Unhealthy', colorClass: 'unhealthy', textClass: 'text-danger', recommendation: 'Health alert! Everyone may experience health effects. Wear a mask.' },
    5: { label: 'Very Unhealthy / Hazardous', colorClass: 'hazardous', textClass: 'text-hazardous', recommendation: 'Health warnings of emergency conditions. Stay indoors.' }
};

const API_BASE_URL = window.location.origin;

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
const unsubscribeBtn = document.getElementById('unsubscribeBtn');

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
if (unsubscribeBtn) {
    unsubscribeBtn.addEventListener('click', handleUnsubscribe);
}

async function handleUnsubscribe() {
    // Auto-fill from Firebase auth if input is empty
    let email = subEmailInput ? subEmailInput.value.trim() : '';
    if (!email && typeof auth !== 'undefined' && auth.currentUser) {
        email = auth.currentUser.email;
        if (subEmailInput) subEmailInput.value = email;
    }
    if (!email) {
        showAlert("Please enter your email to disable alerts.");
        return;
    }

    try {
        unsubscribeBtn.innerText = "Disabling...";
        unsubscribeBtn.disabled = true;
        
        const response = await fetch(`${API_BASE_URL}/unsubscribe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const result = await response.json();
        
        if (result.success) {
            showAlert("✅ Alerts disabled for " + email);
            if (subEmailInput) subEmailInput.value = '';
        } else {
            showAlert(result.message);
        }
    } catch (error) {
        showAlert("Could not connect to subscription service.");
    } finally {
        if (unsubscribeBtn) {
            unsubscribeBtn.innerText = "Disable Alerts";
            unsubscribeBtn.disabled = false;
        }
    }
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
        showAlert("Check if your Backend (app.py) is running on port 8888.");
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
