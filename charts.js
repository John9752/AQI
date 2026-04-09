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
