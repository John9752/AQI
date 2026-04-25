document.addEventListener('DOMContentLoaded', () => {
    
    const API_BASE_URL = "https://aqi-1-6783.onrender.com";

    // Bind UI elements
    const profileName = document.getElementById('profileName');
    const profileEmail = document.getElementById('profileEmail');
    const profileCity = document.getElementById('profileCity');
    const profileThreshold = document.getElementById('profileThreshold');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    const disableAlertsBtn = document.getElementById('disableAlertsBtn');
    const alertContainer = document.getElementById('alertContainer');

    // Make sure we have the backend base link via the auth.js global variables
    //const AUTH_API_BASE_URL = "https://aqi-1-6783.onrender.com";
    let userEmailAddress = "";

    function showAlert(message, isSuccess = false) {
        alertContainer.innerHTML = `
            <div class="alert ${isSuccess ? 'success' : 'danger'}" style="background: ${isSuccess ? 'rgba(16, 185, 129, 0.9)' : 'rgba(239, 68, 68, 0.9)'}">
                <span><strong>${isSuccess ? 'Success:' : 'Warning:'}</strong> ${message}</span>
            </div>
        `;
        setTimeout(() => { alertContainer.innerHTML = ''; }, 5000);
    }

    // 1. Hook into Firebase Authentication State
    auth.onAuthStateChanged(async (user) => {
        if (user) {
            // Populate Authentication Info
            userEmailAddress = user.email;
            profileEmail.value = userEmailAddress;
            profileName.value = user.displayName || "AQI Member";

            // 2. Fetch remote DB preferences
            fetchUserPreferences(userEmailAddress);
        } else {
            // Not logged in -> boot back to Auth!
            const base_url = "https://aqi-1-6783.onrender.com";
            window.location.href = "/login.html";
        }
    });

    async function fetchUserPreferences(email) {
        try {
            const response = await fetch(`${API_BASE_URL}/get_user_preferences?email=${email}`);
            const data = await response.json();
            
            if (data && data.city) {
                profileCity.value = data.city;
                profileThreshold.value = data.threshold || 101;
            }
        } catch (error) {
            console.error("Failed to load preferences:", error);
            showAlert("Could not connect to the backend database to load preferences.");
        }
    }

    // 3. Save remote DB preferences
    saveProfileBtn.addEventListener('click', async () => {
        const city = profileCity.value.trim();
        const threshold = parseInt(profileThreshold.value) || 101;

        if (!city) {
            showAlert("You must define a Default Prediction City.");
            return;
        }

        saveProfileBtn.innerText = "Syncing...";
        saveProfileBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/subscribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    email: userEmailAddress, 
                    city: city,
                    threshold: threshold
                })
            });
            const result = await response.json();
            
            if (result.success) {
                showAlert("Your AI profiling settings have been updated!", true);
            } else {
                showAlert(result.message);
            }
        } catch (error) {
            console.error(error);
            showAlert("Failed to reach Python backend.");
        } finally {
            saveProfileBtn.innerText = "Enable & Sync Hourly Alerts";
            saveProfileBtn.disabled = false;
        }
    });

    // 4. Disable Alerts Logic
    disableAlertsBtn.addEventListener('click', async () => {
        if (!userEmailAddress) {
            showAlert("Please wait for authentication to load.");
            return;
        }

        if (!confirm("Are you sure you want to stop all mail alerts? You can re-enable them anytime.")) {
            return;
        }

        disableAlertsBtn.innerText = "Removing...";
        disableAlertsBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/unsubscribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: userEmailAddress })
            });
            const result = await response.json();
            
            if (result.success) {
                showAlert("Mail alerts have been disabled. You will no longer receive hourly updates.", true);
            } else {
                showAlert(result.message);
            }
        } catch (error) {
            console.error(error);
            showAlert("Failed to reach Python backend.");
        } finally {
            disableAlertsBtn.innerText = "Disable Mail Alerts";
            disableAlertsBtn.disabled = false;
        }
    });
});
