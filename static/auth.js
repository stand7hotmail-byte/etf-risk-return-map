
// Handles all authentication logic, including Firebase init and event listeners

import { registerUser, loginUser, loginGoogle } from './api.js';

// --- Variables ---
let accessToken = localStorage.getItem('access_token');

// --- DOM Elements ---
const authUsernameInput = document.getElementById('auth-username');
const authPasswordInput = document.getElementById('auth-password');
const registerBtn = document.getElementById('register-btn');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const googleLoginBtn = document.getElementById('google-login-btn');
const authMessageDiv = document.getElementById('auth-message');
const loggedInUserDiv = document.getElementById('logged-in-user');

// --- Private Functions ---

function updateAuthUI() {
    const authControlsNavbar = document.getElementById('auth-controls');
    const portfolioManagementSection = document.querySelector('.portfolio-management-section');

    // Clear navbar controls
    authControlsNavbar.innerHTML = '';

    if (accessToken) {
        try {
            const decodedToken = jwt_decode(accessToken);
            // --- Update Navbar ---
            const userInfo = document.createElement('span');
            userInfo.className = 'navbar-text me-3';
            userInfo.textContent = `Welcome, ${decodedToken.sub}`;

            const logoutButtonNavbar = document.createElement('button');
            logoutButtonNavbar.className = 'btn btn-outline-light btn-sm';
            logoutButtonNavbar.textContent = 'Logout';
            logoutButtonNavbar.addEventListener('click', handleLogout);

            authControlsNavbar.appendChild(userInfo);
            authControlsNavbar.appendChild(logoutButtonNavbar);

            // --- Update Main Content ---
            document.querySelector('.auth-section').style.display = 'none';
            portfolioManagementSection.style.display = 'block';

        } catch (e) {
            console.error("Error decoding JWT:", e);
            accessToken = null;
            localStorage.removeItem('access_token');
            authMessageDiv.textContent = 'Invalid token. Please log in again.';
            updateAuthUI(); // Rerun to reset UI
        }
    } else {
        // --- Update Navbar ---
        const loginPrompt = document.createElement('span');
        loginPrompt.className = 'navbar-text text-muted';
        loginPrompt.textContent = 'Please log in to manage portfolios.';
        authControlsNavbar.appendChild(loginPrompt);

        // --- Update Main Content ---
        document.querySelector('.auth-section').style.display = 'block';
        portfolioManagementSection.style.display = 'none';
    }
}

async function handleRegistration() {
    const username = authUsernameInput.value;
    const password = authPasswordInput.value;
    try {
        const result = await registerUser(username, password);
        authMessageDiv.style.color = 'green';
        authMessageDiv.textContent = `User ${result.username} registered successfully!`;
    } catch (error) {
        authMessageDiv.style.color = 'red';
        authMessageDiv.textContent = error.message || 'An error occurred during registration.';
    }
}

async function handleLogin() {
    const username = authUsernameInput.value;
    const password = authPasswordInput.value;
    try {
        const result = await loginUser(username, password);
        accessToken = result.access_token;
        localStorage.setItem('access_token', accessToken);
        authMessageDiv.style.color = 'green';
        authMessageDiv.textContent = 'Logged in successfully!';
        updateAuthUI();
    } catch (error) {
        authMessageDiv.style.color = 'red';
        authMessageDiv.textContent = error.message || 'Login failed.';
    }
}

function handleLogout() {
    accessToken = null;
    localStorage.removeItem('access_token');
    authMessageDiv.style.color = 'green';
    authMessageDiv.textContent = 'Logged out successfully!';
    updateAuthUI();
}

function handleGoogleLogin() {
    const provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider)
        .then(async (result) => {
            const firebaseIdToken = await result.user.getIdToken();
            const data = await loginGoogle(firebaseIdToken);
            accessToken = data.access_token;
            localStorage.setItem('access_token', accessToken);
            authMessageDiv.style.color = 'green';
            authMessageDiv.textContent = 'Logged in successfully with Google!';
            updateAuthUI();
        })
        .catch((error) => {
            console.error('Google Sign-In Error:', error);
            authMessageDiv.style.color = 'red';
            authMessageDiv.textContent = `Google login error: ${error.message}`;
        });
}

// --- Public Functions ---

export function initAuth() {
    // Firebase Configuration
    const firebaseConfig = {
      apiKey: "AIzaSyAwlMjilSEaZlSXnEC4NQgOV_gwYqLQ1co", // This should be handled securely
      authDomain: "etf-webapp.firebaseapp.com",
      projectId: "etf-webapp",
      storageBucket: "etf-webapp.appspot.com",
      messagingSenderId: "761377330809",
      appId: "1:761377330809:web:cd0f5a80a6c105ab2aa6a8"
    };

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);

    // Attach event listeners
    registerBtn.addEventListener('click', handleRegistration);
    loginBtn.addEventListener('click', handleLogin);
    logoutBtn.addEventListener('click', handleLogout);
    googleLoginBtn.addEventListener('click', handleGoogleLogin);

    // Initial UI update on page load
    updateAuthUI();
}
