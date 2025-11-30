// -*- coding: utf-8 -*-
/**
 * JavaScript module for the broker comparison page.
 * Handles fetching broker data, dynamic rendering, filtering, sorting, and affiliate click tracking.
 */

import * as api from './api.js'; // Assuming api.js provides fetch wrappers
import * as theme from './theme.js'; // For theme-related functionalities
import * as analytics from './analytics.js'; // Import analytics module

// DOM Elements
const brokerCardsContainer = document.getElementById('broker-cards-container');
const comparisonTableBody = document.getElementById('comparison-table-body');
const regionTabsContainer = document.getElementById('regionTabs');
const loadingSpinner = document.getElementById('loading-spinner');
const brokerComparisonTable = document.getElementById('broker-comparison-table');

let allBrokers = []; // Stores all fetched brokers

/**
 * Shows or hides the loading spinner.
 * @param {boolean} show - True to show, false to hide.
 */
function showLoadingSpinner(show) {
    if (loadingSpinner) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }
}

/**
 * Detects user's likely region based on browser language.
 * @returns {string} The detected region code (e.g., "US", "JP"). Defaults to "US".
 */
function detectUserRegion() {
    const lang = navigator.language || navigator.userLanguage;
    if (lang.startsWith('ja')) return 'JP';
    if (lang.startsWith('en')) return 'US'; // Default to US for English speakers
    return 'US';
}


/**
 * Fetches broker data from the API.
 * @param {string} region - The region to filter brokers by (e.g., "US", "JP").
 * @returns {Promise<Array>} - A promise that resolves to an array of broker objects.
 */
async function fetchBrokers(region) {
    showLoadingSpinner(true);
    try {
        const response = await api.get('/api/brokers', { region: region, active_only: true });
        return response.brokers; // Assuming the API returns { brokers: [...] }
    } catch (error) {
        console.error('Error fetching brokers:', error);
        // Display an error message to the user
        brokerCardsContainer.innerHTML = `<div class="alert alert-danger" role="alert">
            証券会社情報の取得中にエラーが発生しました。しばらくしてからもう一度お試しください。
        </div>`;
        return [];
    } finally {
        showLoadingSpinner(false);
    }
}

/**
 * Creates an HTML element for a single broker card.
 * @param {object} broker - Broker data.
 * @returns {HTMLElement} - The created card element.
 */
function createBrokerCard(broker) {
    const card = document.createElement('div');
    card.className = 'col-md-6 col-lg-4 d-flex'; // Flex to ensure equal height cards
    card.innerHTML = `
        <div class="broker-card flex-fill">
            <div class="d-flex align-items-center mb-2">
                ${broker.logo_url ? `<img src="${broker.logo_url}" alt="${broker.display_name} logo" class="me-2">` : `<i class="bi bi-bank fs-3 me-2"></i>`}
                <h5 class="card-title mb-0">${broker.display_name}</h5>
            </div>
            <p class="text-muted small">${broker.description}</p>
            <div class="mb-2">
                ${JSON.parse(broker.pros).map(p => `<span class="badge bg-success-subtle text-success me-1 mb-1">${p}</span>`).join('')}
            </div>
            <p class="small"><strong>最適な人:</strong> ${broker.best_for}</p>
            <p class="small"><strong>評価:</strong> ${'⭐'.repeat(Math.round(broker.rating))} (${broker.rating})</p>
            <a href="#" class="btn btn-primary btn-sm mt-auto affiliate-link" 
               data-broker-id="${broker.id}" data-placement="broker_page">
                口座開設する（無料）
                <span class="badge bg-info ms-1">AD</span>
            </a>
        </div>
    `;
    const affiliateLink = card.querySelector('.affiliate-link');
    if (affiliateLink) {
        affiliateLink.addEventListener('click', (e) => {
            e.preventDefault();
            analytics.trackAffiliateClick(broker, 'broker_page')
                .then(response => {
                    if (response.redirect_url) {
                        window.location.href = response.redirect_url;
                    } else {
                        window.location.href = broker.affiliate_url; // Fallback to direct URL
                    }
                })
                .catch(() => {
                    window.location.href = broker.affiliate_url; // Fallback on error
                });
        });
    }
    return card;
}

/**
 * Creates an HTML table row for a single broker in the comparison table.
 * @param {object} broker - Broker data.
 * @returns {HTMLElement} - The created table row element.
 */
function createBrokerTableRow(broker) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            ${broker.logo_url ? `<img src="${broker.logo_url}" alt="${broker.display_name} logo" style="max-height: 30px; vertical-align: middle;" class="me-2">` : ''}
            ${broker.display_name}
        </td>
        <td>${broker.commission_rate > 0 ? `${broker.commission_rate} ${broker.region === 'JP' ? '円' : '$'}` : '要確認'}</td>
        <td>${JSON.parse(broker.pros).length}+</td> <!-- Assuming pros roughly indicates feature count -->
        <td>${broker.best_for}</td>
        <td>${'⭐'.repeat(Math.round(broker.rating))}</td>
        <td>
            <a href="#" class="btn btn-sm btn-outline-primary affiliate-link" 
               data-broker-id="${broker.id}" data-placement="broker_table">
                口座開設
                <span class="badge bg-info ms-1">AD</span>
            </a>
        </td>
    `;
     const affiliateLink = row.querySelector('.affiliate-link');
    if (affiliateLink) {
        affiliateLink.addEventListener('click', (e) => {
            e.preventDefault();
            analytics.trackAffiliateClick(broker, 'broker_table')
                .then(response => {
                    if (response.redirect_url) {
                        window.location.href = response.redirect_url;
                    } else {
                        window.location.href = broker.affiliate_url; // Fallback to direct URL
                    }
                })
                .catch(() => {
                    window.location.href = broker.affiliate_url; // Fallback on error
                });
        });
    }
    return row;
}

/**
 * Renders the fetched brokers into cards and the comparison table.
 * @param {Array} brokers - An array of broker objects.
 */
function renderBrokers(brokers) {
    brokerCardsContainer.innerHTML = '';
    comparisonTableBody.innerHTML = '';

    brokers.forEach(broker => {
        brokerCardsContainer.appendChild(createBrokerCard(broker));
        comparisonTableBody.appendChild(createBrokerTableRow(broker));
    });
    allBrokers = brokers; // Store for sorting
}

/**
 * Handles region tab switching.
 * @param {Event} event - The click event.
 */
async function handleRegionTabClick(event) {
    const target = event.target;
    if (target.tagName === 'BUTTON' && target.closest('#regionTabs')) {
        const region = target.dataset.region;
        if (region) {
            const brokers = await fetchBrokers(region);
            renderBrokers(brokers);
        }
    }
}

let currentSortColumn = null;
let currentSortDirection = 'asc'; // 'asc' or 'desc'

/**
 * Sorts the broker comparison table.
 * @param {string} sortBy - The column key to sort by (e.g., 'display_name', 'rating').
 */
function sortBrokers(sortBy) {
    if (currentSortColumn === sortBy) {
        currentSortDirection = (currentSortDirection === 'asc') ? 'desc' : 'asc';
    } else {
        currentSortColumn = sortBy;
        currentSortDirection = 'asc';
    }

    const sortedBrokers = [...allBrokers].sort((a, b) => {
        let valA = a[sortBy];
        let valB = b[sortBy];

        // Custom handling for specific types if necessary (e.g., numeric vs string)
        if (typeof valA === 'string') {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
        }

        if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
        if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });
    renderBrokers(sortedBrokers); // Re-render sorted data

    // Update sort icons in table header
    const headers = brokerComparisonTable.querySelectorAll('th[data-sort-by]');
    headers.forEach(header => {
        const icon = header.querySelector('i');
        if (icon) {
            icon.className = 'bi bi-arrow-down-up'; // Reset all
        }
        if (header.dataset.sortBy === currentSortColumn && icon) {
            icon.className = currentSortDirection === 'asc' ? 'bi bi-arrow-up' : 'bi bi-arrow-down';
        }
    });
}

/**
 * Sets up all event listeners for the page.
 */
function setupEventListeners() {
    regionTabsContainer.addEventListener('click', handleRegionTabClick);

    // Setup sortable table headers
    const sortableHeaders = brokerComparisonTable.querySelectorAll('th[data-sort-by]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            const sortBy = header.dataset.sortBy;
            if (sortBy) {
                sortBrokers(sortBy);
            }
        });
    });
}
/**
 * Sets up all event listeners for the page.
 */
function setupEventListeners() {
    regionTabsContainer.addEventListener('click', handleRegionTabClick);

    // Setup sortable table headers
    const sortableHeaders = brokerComparisonTable.querySelectorAll('th[data-sort-by]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => {
            const sortBy = header.dataset.sortBy;
            if (sortBy) {
                sortBrokers(sortBy);
            }
        });
    });
}


// Initialize page on DOMContentLoaded
document.addEventListener('DOMContentLoaded', async () => {
    theme.loadSavedTheme(); // Apply saved theme
    setupEventListeners();

    // Track page view for the brokers page
    analytics.trackPageView("Broker Comparison Page");

    // Load brokers for the default region (e.g., "US")
    const defaultRegion = detectUserRegion();
    // Activate the corresponding tab
    const defaultTabButton = regionTabsContainer.querySelector(`button[data-region="${defaultRegion}"]`);
    if (defaultTabButton) {
        new bootstrap.Tab(defaultTabButton).show();
    }
    
    const brokers = await fetchBrokers(defaultRegion);
    renderBrokers(brokers);
});
