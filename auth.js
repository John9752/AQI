// ==========================================
// FIREBASE CONFIGURATION
// ==========================================
// TODO: Replace this with your actual Firebase project configuration
// Import the functions you need from the SDKs you need
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyD_-ESrrNtvjeTjlJMf6X9Ln-278RB6JbY",
    authDomain: "aqi-dti.firebaseapp.com",
    projectId: "aqi-dti",
    storageBucket: "aqi-dti.firebasestorage.app",
    messagingSenderId: "516835339642",
    appId: "1:516835339642:web:21e22cd5694aa85ca47ac3",
    measurementId: "G-9R2WJ3RGPR"
};

// Initialize Firebase only if it hasn't been initialized
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const auth = firebase.auth();

// ==========================================
// ELEMENT SELECTION
// ==========================================
const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');
const authError = document.getElementById('authError');
const logoutBtn = document.getElementById('logoutBtn');

// ==========================================
// ROUTE GUARDING
// ==========================================
const currentPath = window.location.pathname;
const isAuthPage = currentPath.includes('login.html') || currentPath.includes('signup.html');

auth.onAuthStateChanged((user) => {
    if (user) {
        // User is signed in
        if (isAuthPage) {
            window.location.href = 'index.html'; // Redirect to dashboard
        }
    } else {
        // User is signed out
        if (!isAuthPage) {
            window.location.href = 'login.html'; // Redirect to login
        }
    }
});

// ==========================================
// LOGIN LOGIC
// ==========================================
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Visual loading state
        const btn = loginForm.querySelector('button');
        const originalText = btn.innerText;
        btn.innerText = 'Logging in...';
        btn.disabled = true;

        try {
            await auth.signInWithEmailAndPassword(email, password);
            // onAuthStateChanged will handle the redirect
        } catch (error) {
            authError.innerHTML = "<strong>Invalid login credentials</strong>";
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });
}

// ==========================================
// SIGNUP LOGIC
// ==========================================
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (password.length < 6) {
            authError.innerText = "Password should be at least 6 characters.";
            return;
        }

        // Visual loading state
        const btn = signupForm.querySelector('button');
        const originalText = btn.innerText;
        btn.innerText = 'Creating account...';
        btn.disabled = true;

        try {
            const userCredential = await auth.createUserWithEmailAndPassword(email, password);
            // Optionally update user profile with the name
            await userCredential.user.updateProfile({
                displayName: name
            });

            // Trigger Welcome Email via Backend
            try {
                fetch(`${AUTH_API_BASE_URL}/send_welcome`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email, name: name })
                });
            } catch (err) {
                console.error("Failed to trigger welcome email:", err);
            }

            // onAuthStateChanged will handle the redirect
        } catch (error) {
            authError.innerText = error.message;
            btn.innerText = originalText;
            btn.disabled = false;
        }
    });
}

// ==========================================
// BACKEND BASE URL
// ==========================================
const AUTH_BACKEND_ORIGINS = ['http://127.0.0.1:5000', 'http://localhost:5000'];
const AUTH_API_BASE_URL = AUTH_BACKEND_ORIGINS.includes(window.location.origin)
    ? ''
    : 'http://127.0.0.1:5000';

// ==========================================
// LOGOUT LOGIC
// ==========================================
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        auth.signOut().then(() => {
            // onAuthStateChanged will handle the redirect
        }).catch((error) => {
            console.error('Sign Out Error', error);
        });
    });
}

