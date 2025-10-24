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
    const icon = themeToggler.querySelector('i');
    if (theme === 'dark') {
        icon.classList.remove('bi-sun-fill');
        icon.classList.add('bi-moon-stars-fill');
    } else {
        icon.classList.remove('bi-moon-stars-fill');
        icon.classList.add('bi-sun-fill');
    }
}

// Event listener for the toggler button
themeToggler.addEventListener('click', () => {
    const currentTheme = getCurrentTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
});

// On page load, set the theme from localStorage or default to light
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
});
