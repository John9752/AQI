// Global instances to manage chart lifecycle
let pollutantsChart = null;
let trendChart = null;
let areaChart = null;
let mapInstance = null;
let vizagForecastChart = null;

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
        options: {
            ...getCommonOptions('Pollutants Concentration'),
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.parsed.y} μg/m³`;
                        }
                    }
                }
            }
        }
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
// DATA MAPPING & CONFIGURATION (Dual Standards)
// ==========================================
const AQI_MAPPING = {
    'IN': { // Indian National AQI (CPCB)
        1: { label: 'Good', colorClass: 'aqi-1', textClass: 'text-1', recommendation: 'Air quality is satisfactory. Pose little or no risk.' },
        2: { label: 'Satisfactory', colorClass: 'aqi-2', textClass: 'text-2', recommendation: 'Sensitive people may experience minor breathing discomfort.' },
        3: { label: 'Moderate', colorClass: 'aqi-3', textClass: 'text-3', recommendation: 'May cause breathing discomfort to people with lungs/asthma/heart diseases.' },
        4: { label: 'Poor', colorClass: 'aqi-4', textClass: 'text-4', recommendation: 'May cause breathing discomfort to most people on prolonged exposure.' },
        5: { label: 'Very Poor', colorClass: 'aqi-5', textClass: 'text-5', recommendation: 'May cause respiratory illness on prolonged exposure.' },
        6: { label: 'Severe', colorClass: 'aqi-6', textClass: 'text-6', recommendation: 'Affects healthy people and seriously impacts those with existing diseases.' }
    },
    'INTL': { // US EPA / International
        1: { label: 'Good', colorClass: 'aqi-1', textClass: 'text-1', recommendation: 'Air quality is satisfactory. Ideal for outdoor activities.' },
        2: { label: 'Moderate', colorClass: 'aqi-2', textClass: 'text-2', recommendation: 'Sensitive individuals should limit prolonged outdoor exertion.' },
        3: { label: 'Unhealthy (Sensitive)', colorClass: 'aqi-3', textClass: 'text-3', recommendation: 'Sensitive groups may experience health effects. Limit exertion.' },
        4: { label: 'Unhealthy', colorClass: 'aqi-4', textClass: 'text-4', recommendation: 'Everyone may experience health effects. Wear a mask.' },
        5: { label: 'Very Unhealthy', colorClass: 'aqi-5', textClass: 'text-5', recommendation: 'Health warnings of emergency conditions. Stay indoors.' }
    }
};

const API_BASE_URL = "https://aqi-1-6783.onrender.com";

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
        console.log(`Fetching data for: ${city}`);
        
        // Use the endpoint that supports source attribution and requested_name
        const response = await fetch(`${API_BASE_URL}/get_current_aqi?city=${encodeURIComponent(city)}`);
        const data = await response.json();

        if (data.error) {
            showAlert(data.error);
            return;
        }

        // Update main dashboard UI
        updateUI(data);

        // Notify chart and map components
        document.dispatchEvent(new CustomEvent('renderPollutants', { detail: data.components }));
        document.dispatchEvent(new CustomEvent('renderMap', { detail: { coordinates: data.coordinates, city: data.city, level: data.level } }));
        
        // Trigger AI Prediction
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
        // fetchPrediction(componentsForPredict);
        // fetchPrediction removed
        
        // Fetch historical trends using the name hint to ensure DB match
        const trendsName = data.requested_name || city;
        fetchTrendData(trendsName);

    } catch (error) {
        console.error("Fetch Error:", error);
        showAlert("Check if your Backend is running.");
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
        // fetchPrediction(componentsForPredict);
        // fetchPrediction removed
        
        // Fetch Trends for the area using the specific location name
        fetchTrendData(data.city);

    } catch (error) {
        console.error("Coords Fetch Error:", error);
    }
}

async function fetchTrendData(city) {
    try {
        const trendContainer = document.getElementById('trendChartContainer');
        if (trendContainer && !document.getElementById('trendChart')) {
             trendContainer.innerHTML = '<canvas id="trendChart"></canvas>';
        }

        const response = await fetch(`${API_BASE_URL}/aqi_trends?city=${encodeURIComponent(city)}`);
        const trends = await response.json();
        
        if (trends && trends.length > 0) {
            document.dispatchEvent(new CustomEvent('renderTrends', { detail: trends }));
        } else {
             console.log("No trend data returned for", city);
             // Optionally show a placeholder if empty
        }
    } catch (error) {
        console.warn("Could not fetch trends:", error);
    }
}

function updateUI(data) {
    // Extract country from location string (e.g., "Visakhapatnam, IN")
    const isIndia = data.city.includes(', IN');
    const mappingProfile = isIndia ? AQI_MAPPING['IN'] : AQI_MAPPING['INTL'];
    const config = mappingProfile[data.level] || mappingProfile[1];
    
    cityNameDisplay.textContent = data.city;
    aqiValueDisplay.textContent = Math.round(data.aqi);
    aqiStatusDisplay.textContent = data.category || config.label;
    healthRecDisplay.textContent = data.health_message || config.recommendation;

    // Use dominant pollutant correctly evaluated by CPCB breakpoints
    if (data.dominant_pollutant) {
        const mainPName = document.getElementById('mainPollutantName');
        const mainPCont = document.getElementById('mainPollutantContainer');
        if (mainPName && mainPCont) {
            mainPName.textContent = data.dominant_pollutant;
            mainPCont.style.display = 'block';
        }
    }



    // Reset styles
    aqiCircle.className = 'aqi-circle';
    aqiStatusDisplay.className = 'aqi-status';
    
    // Apply dynamic classes
    aqiCircle.classList.add(config.colorClass);
    aqiStatusDisplay.classList.add(config.textClass);

    // Visual Alert logic
    alertContainer.innerHTML = '';
    const alertThreshold = isIndia ? 4 : 3; // Trigger earlier for International standards 
    if (data.level >= alertThreshold) {
        alertContainer.innerHTML = `
            <div class="alert">
                <span><strong>High Pollution Alert:</strong> ${config.recommendation}</span>
            </div>
        `;
    }

    // Trigger Dynamic Background Animation
    if (window.aqiAnimator) {
        window.aqiAnimator.setAQILevel(data.level);
    }
}

async function handleSubscription() {
    const email = subEmailInput.value.trim();
    const city = cityNameDisplay.textContent.trim();

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



async function loadVizag10YrForecast(area) {
    if (!area) area = 'Visakhapatnam';
    const ctx = document.getElementById('vizagForecastChart')?.getContext('2d');
    if (!ctx) return;

    try {
        const response = await fetch(`${API_BASE_URL}/vizag_10yr_forecast?area=${encodeURIComponent(area)}`);
        const data = await response.json();
        
        if (data.error || !data.years) return;

        if (vizagForecastChart) {
            vizagForecastChart.destroy();
        }

        // Show area info
        const infoBox = document.getElementById('vizagForecastInfo');
        const nameEl = document.getElementById('vizagForecastAreaName');
        const baseEl = document.getElementById('vizagForecastBaseline');
        if (infoBox && nameEl) {
            infoBox.style.display = 'block';
            nameEl.textContent = `📍 ${data.area}`;
            if (baseEl) baseEl.textContent = `(Baseline: ${data.baseline_mean} AQI · σ ${data.baseline_std})`;
        }

        // Color based on average AQI
        const avgAqi = data.forecast.reduce((a, b) => a + b, 0) / data.forecast.length;
        let lineColor = '#10b981';
        if (avgAqi > 200) lineColor = '#ef4444';
        else if (avgAqi > 100) lineColor = '#f59e0b';
        else if (avgAqi > 50) lineColor = '#fbbf24';

        // Gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, lineColor + '40');
        gradient.addColorStop(1, lineColor + '05');

        vizagForecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.years,
                datasets: [{
                    label: data.area + ' AQI',
                    data: data.forecast,
                    borderColor: lineColor,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    tension: 0.35,
                    pointRadius: 5,
                    pointBackgroundColor: lineColor,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 8,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#cbd5e1', font: { size: 13, weight: 'bold' } }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 },
                        callbacks: {
                            label: function(context) {
                                const val = context.parsed.y;
                                let cat = 'Good';
                                if (val > 400) cat = 'Severe';
                                else if (val > 300) cat = 'Very Poor';
                                else if (val > 200) cat = 'Poor';
                                else if (val > 100) cat = 'Moderate';
                                else if (val > 50) cat = 'Satisfactory';
                                return `AQI: ${val} (${cat})`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94a3b8', font: { size: 12 } },
                        grid: { display: false }
                    },
                    y: {
                        ticks: { color: '#94a3b8', font: { size: 12 } },
                        grid: { color: 'rgba(255, 255, 255, 0.06)' },
                        beginAtZero: true
                    }
                }
            }
        });

    } catch (e) {
        console.warn(`Could not load forecast for ${area}.`, e);
    }
}

async function initVizagDateLookup() {
    const select = document.getElementById('vizagAreaSelect');
    const predictBtn = document.getElementById('vizagPredictBtn');
    const dateInput = document.getElementById('vizagDateInput');
    const resultDisplay = document.getElementById('vizagSpecificResult');
    const searchInput = document.getElementById('vizagAreaSearch');
    const datalist = document.getElementById('vizagAreaList');
    const showForecastBtn = document.getElementById('vizagShowForecastBtn');

    if (!select || !predictBtn) return;

    // Fetch all areas from backend
    let allAreas = [];
    try {
        const res = await fetch(`${API_BASE_URL}/forecast_areas`);
        const data = await res.json();
        if (data.areas) {
            allAreas = data.areas;
            // Populate the datalist for autocomplete search
            if (datalist) {
                allAreas.forEach(area => {
                    const opt = document.createElement('option');
                    opt.value = area;
                    datalist.appendChild(opt);
                });
            }
            // Populate the select dropdown for date prediction
            allAreas.forEach(area => {
                const option = document.createElement('option');
                option.value = area;
                option.textContent = area;
                select.appendChild(option);
            });
        }
    } catch (e) {
        console.warn('Could not load forecast areas', e);
    }

    // Show Forecast button: search area and render its chart
    if (showForecastBtn && searchInput) {
        showForecastBtn.addEventListener('click', () => {
            const area = searchInput.value.trim();
            if (area) {
                loadVizag10YrForecast(area);
                // Also sync the date prediction dropdown
                select.value = area;
            }
        });
        // Also trigger on Enter key
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                showForecastBtn.click();
            }
        });
    }

    // Set default date to today + 1 year
    const defaultDate = new Date();
    defaultDate.setFullYear(defaultDate.getFullYear() + 1);
    dateInput.value = defaultDate.toISOString().split('T')[0];

    // Date prediction button
    predictBtn.addEventListener('click', async () => {
        const area = select.value;
        const date = dateInput.value;

        if (!date) {
            resultDisplay.textContent = 'Select a date!';
            return;
        }

        const yr = parseInt(date.split('-')[0]);
        if (yr < 2026 || yr > 2036) {
            resultDisplay.textContent = 'Pick 2026\u20132036';
            return;
        }

        predictBtn.textContent = '\u23f3...';
        predictBtn.disabled = true;
        resultDisplay.textContent = '--';

        try {
            const response = await fetch(`${API_BASE_URL}/vizag_date_prediction?area=${encodeURIComponent(area)}&date=${date}`);
            const data = await response.json();

            if (data.error) {
                resultDisplay.textContent = 'Error';
                return;
            }

            const aqi = data.predicted_aqi;
            const category = data.category || '';

            let color = '#10b981';
            if (aqi > 400) color = '#7f1d1d';
            else if (aqi > 300) color = '#8b5cf6';
            else if (aqi > 200) color = '#ef4444';
            else if (aqi > 100) color = '#f59e0b';
            else if (aqi > 50)  color = '#fbbf24';

            resultDisplay.style.color = color;
            resultDisplay.title = `${area} on ${date}: AQI ${aqi} (${category})`;
            resultDisplay.textContent = `${aqi} \u00b7 ${category}`;

        } catch (e) {
            resultDisplay.textContent = 'Error';
            console.error('Date prediction error', e);
        } finally {
            predictBtn.textContent = '\ud83d\udd0d Predict AQI';
            predictBtn.disabled = false;
        }
    });
}

// Initial Load
window.addEventListener('load', () => {
    if (cityInput) {
        cityInput.value = 'Visakhapatnam';
        fetchDashboardData('Visakhapatnam');
        loadVizag10YrForecast('Visakhapatnam');
        initVizagDateLookup();
    }
});
