const themeToggler = document.getElementById('theme-toggler');
const htmlElement = document.documentElement;

// Function to get the current theme
export function getCurrentTheme() {
    return htmlElement.getAttribute('data-bs-theme');
}

// Function to set the theme
function setTheme(theme) {
    htmlElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);

    // Update the icon
    if (themeToggler) { // Check if toggler exists on the page
        const icon = themeToggler.querySelector('i');
        if (icon) { // Check if icon exists before manipulating
            if (theme === 'dark') {
                icon.classList.remove('bi-sun-fill');
                icon.classList.add('bi-moon-stars-fill');
            } else {
                icon.classList.remove('bi-moon-stars-fill');
                icon.classList.add('bi-sun-fill');
            }
        }
    }
}

/**
 * Loads the saved theme from localStorage and applies it.
 * Defaults to 'light' if no theme is saved.
 */
export function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}

// Event listener for the toggler button
if (themeToggler) {
    themeToggler.addEventListener('click', () => {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });
}

// Immediately apply the saved theme on script load.
loadSavedTheme();