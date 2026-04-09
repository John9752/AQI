// Listen for event from script.js
document.addEventListener('predictTomorrowAQI', (e) => {
    const currentAqi = e.detail.currentAqi;
    predictAQI(currentAqi);
});

function predictAQI(currentAqi) {
    const tomorrowElement = document.getElementById('tomorrowAqi');
    const trendTextElement = document.getElementById('trendText');
    const trendIconElement = document.getElementById('trendIcon');
    
    if (!tomorrowElement || !trendTextElement || !trendIconElement) return;

    // Simulate an AI Model / Machine Learning prediction using basic statistics/random walk
    // In a real application, you'd fetch from a backend API running an ML model (e.g. ARIMA, LSTM)
    // based on historical historical air quality and weather forecasts.
    
    // For demo purposes, we will add a random drift to the current AQI to project tomorrow's value.
    const drift = (Math.random() - 0.5) * 40; // Random change between -20 and +20
    let predictedAqi = Math.round(currentAqi + drift);
    
    // Bounds checking
    if (predictedAqi < 0) predictedAqi = 0;
    if (predictedAqi > 500) predictedAqi = 500;

    tomorrowElement.textContent = `AQI: ${predictedAqi}`;

    if (predictedAqi > currentAqi + 10) {
        trendTextElement.textContent = "Forecast indicates worsening air quality. Keep masks ready.";
        trendIconElement.textContent = "📈";
        trendTextElement.style.color = "#ef4444"; // Redish
    } else if (predictedAqi < currentAqi - 10) {
        trendTextElement.textContent = "Forecast indicates improving air quality. Great for outdoor plans!";
        trendIconElement.textContent = "📉";
        trendTextElement.style.color = "#10b981"; // Greenish
    } else {
        trendTextElement.textContent = "Air quality is expected to remain stable.";
        trendIconElement.textContent = "➡️";
        trendTextElement.style.color = "#cbd5e1"; // Neutral
    }
}
