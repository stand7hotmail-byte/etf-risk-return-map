// -*- coding: utf-8 -*-
/**
 * JavaScript module for the Admin Affiliate Dashboard.
 * Handles fetching data, rendering charts, and updating UI elements.
 */

import * as api from '../api.js'; // Assuming api.js provides fetch wrappers
import * as theme from '../theme.js'; // For theme-related functionalities

// DOM Elements
const totalClicksElem = document.getElementById('total-clicks');
const totalConversionsElem = document.getElementById('total-conversions');
const conversionRateElem = document.getElementById('conversion-rate');
const estimatedRevenueElem = document.getElementById('estimated-revenue');
const dateRangePresetSelect = document.getElementById('date-range-preset');
const customStartDateGroup = document.getElementById('custom-start-date-group');
const customEndDateGroup = document.getElementById('custom-end-date-group');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const brokerDetailsTableBody = document.getElementById('broker-details-table-body');

// Chart instances
let clicksChart;
let brokerPerformanceChart;
let placementClicksChart;
let brokerConversionsChart;


/**
 * Formats a date to YYYY-MM-DD string.
 * @param {Date} date - The date object.
 * @returns {string} Formatted date string.
 */
function formatDate(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

/**
 * Calculates start and end dates based on a preset.
 * @param {string} preset - The preset string (e.g., "7d", "30d", "90d").
 * @returns {{startDate: string, endDate: string}}
 */
function getDateRange(preset) {
    const endDate = new Date();
    let startDate = new Date();

    if (preset === "7d") {
        startDate.setDate(endDate.getDate() - 6);
    } else if (preset === "30d") {
        startDate.setDate(endDate.getDate() - 29);
    } else if (preset === "90d") {
        startDate.setDate(endDate.getDate() - 89);
    } else if (preset === "custom") {
        return {
            startDate: startDateInput.value,
            endDate: endDateInput.value
        };
    }
    return { startDate: formatDate(startDate), endDate: formatDate(endDate) };
}

/**
 * Loads and displays dashboard data.
 */
async function loadDashboardData() {
    const preset = dateRangePresetSelect.value;
    const { startDate, endDate } = getDateRange(preset);

    try {
        const stats = await api.get('/api/admin/affiliate/stats', {
            start_date: startDate,
            end_date: endDate
        });
        
        updateSummaryCards(stats);
        renderClicksOverTimeChart(stats);
        renderBrokerPerformanceChart(stats.by_broker);
        renderPlacementClicksChart(stats.by_placement);
        renderBrokerConversionsChart(stats.by_broker);
        populateBrokerDetailsTable(stats.by_broker);

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        // Display an error message on the dashboard
        alert('ダッシュボードデータの取得中にエラーが発生しました。');
    }
}

/**
 * Updates the summary cards with fetched data.
 * @param {object} stats - The statistics object.
 */
function updateSummaryCards(stats) {
    totalClicksElem.textContent = stats.total_clicks.toLocaleString();
    totalConversionsElem.textContent = stats.total_conversions.toLocaleString();
    conversionRateElem.textContent = `${stats.conversion_rate.toFixed(2)}%`;
    estimatedRevenueElem.textContent = `$${stats.estimated_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Renders the Clicks Over Time chart.
 * @param {object} stats - The statistics object.
 */
function renderClicksOverTimeChart(stats) {
    const ctx = document.getElementById('clicks-over-time-chart').getContext('2d');
    const dates = []; // You'll need to transform your data to get daily clicks
    const clicks = []; // You'll need to transform your data to get daily clicks

    // Example transformation assuming stats.by_broker gives daily clicks
    // This part of the data is not directly provided by the current /api/admin/affiliate/stats schema
    // So for now, we'll just show a dummy chart or aggregate if possible
    // For a real implementation, the API would need to return daily aggregates.
    // For this example, let's use a simplified approach or placeholder if not directly calculable.

    // If API endpoint for stats returned daily data, it would look like:
    // stats = { ..., daily_clicks: [{date: "YYYY-MM-DD", count: 10}] }
    // For now, let's just make a very basic chart with total counts if daily data is not available.
    
    // As the current API doesn't return time-series data for clicks,
    // this chart will remain a placeholder or display aggregated data.
    // To implement this fully, the backend /api/admin/affiliate/stats should return
    // an array of {date: string, clicks: int} for the period.

    // Dummy data for now:
    const data = {
        labels: [stats.period.start.split('T')[0], stats.period.end.split('T')[0]], // From the period start/end
        datasets: [{
            label: 'Total Clicks',
            data: [0, stats.total_clicks], // Simple start to end
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
            fill: false
        }]
    };

    if (clicksChart) {
        clicksChart.destroy();
    }
    clicksChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'day'
                    },
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Clicks'
                    }
                }
            }
        }
    });
}

/**
 * Renders the Broker Performance chart.
 * @param {Array} byBroker - Array of BrokerPerformanceStats.
 */
function renderBrokerPerformanceChart(byBroker) {
    const ctx = document.getElementById('broker-performance-chart').getContext('2d');
    const labels = byBroker.map(b => b.display_name || b.broker_name);
    const data = {
        labels: labels,
        datasets: [{
            label: 'Estimated Revenue',
            data: byBroker.map(b => b.revenue),
            backgroundColor: 'rgba(255, 159, 64, 0.6)',
            borderColor: 'rgba(255, 159, 64, 1)',
            borderWidth: 1
        }]
    };

    if (brokerPerformanceChart) {
        brokerPerformanceChart.destroy();
    }
    brokerPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Estimated Revenue ($)'
                    }
                }
            }
        }
    });
}

/**
 * Renders the Placement Clicks chart (Pie chart).
 * @param {Array} byPlacement - Array of PlacementPerformanceStats.
 */
function renderPlacementClicksChart(byPlacement) {
    const ctx = document.getElementById('placement-clicks-chart').getContext('2d');
    const labels = byPlacement.map(p => p.placement);
    const data = {
        labels: labels,
        datasets: [{
            data: byPlacement.map(p => p.clicks),
            backgroundColor: [
                'rgba(255, 99, 132, 0.6)',
                'rgba(54, 162, 235, 0.6)',
                'rgba(255, 206, 86, 0.6)',
                'rgba(75, 192, 192, 0.6)',
                'rgba(153, 102, 255, 0.6)',
                'rgba(255, 159, 64, 0.6)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
        }]
    };

    if (placementClicksChart) {
        placementClicksChart.destroy();
    }
    placementClicksChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Clicks by Placement'
                }
            }
        }
    });
}

/**
 * Renders the Broker Conversions chart (Pie chart).
 * @param {Array} byBroker - Array of BrokerPerformanceStats.
 */
function renderBrokerConversionsChart(byBroker) {
    const ctx = document.getElementById('broker-conversions-chart').getContext('2d');
    const labels = byBroker.map(b => b.display_name || b.broker_name);
    const data = {
        labels: labels,
        datasets: [{
            data: byBroker.map(b => b.conversions),
            backgroundColor: [
                'rgba(100, 200, 100, 0.6)',
                'rgba(200, 100, 100, 0.6)',
                'rgba(100, 100, 200, 0.6)',
                'rgba(200, 200, 100, 0.6)',
                'rgba(100, 200, 200, 0.6)',
                'rgba(200, 100, 200, 0.6)'
            ],
            borderColor: [
                'rgba(100, 200, 100, 1)',
                'rgba(200, 100, 100, 1)',
                'rgba(100, 100, 200, 1)',
                'rgba(200, 200, 100, 1)',
                'rgba(100, 200, 200, 1)',
                'rgba(200, 100, 200, 1)'
            ],
            borderWidth: 1
        }]
    };

    if (brokerConversionsChart) {
        brokerConversionsChart.destroy();
    }
    brokerConversionsChart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Conversions by Broker'
                }
            }
        }
    });
}


/**
 * Populates the broker details table.
 * @param {Array} byBroker - Array of BrokerPerformanceStats.
 */
function populateBrokerDetailsTable(byBroker) {
    brokerDetailsTableBody.innerHTML = '';
    if (byBroker.length === 0) {
        brokerDetailsTableBody.innerHTML = '<tr><td colspan="5" class="text-center">データがありません</td></tr>';
        return;
    }
    byBroker.forEach(b => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${b.display_name || b.broker_name}</td>
            <td>${b.clicks.toLocaleString()}</td>
            <td>${b.conversions.toLocaleString()}</td>
            <td>${b.conversion_rate.toFixed(2)}%</td>
            <td>$${b.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        `;
        brokerDetailsTableBody.appendChild(row);
    });
}

/**
 * Sets up event listeners for date range selection.
 */
function setupEventListeners() {
    dateRangePresetSelect.addEventListener('change', () => {
        if (dateRangePresetSelect.value === 'custom') {
            customStartDateGroup.style.display = 'block';
            customEndDateGroup.style.display = 'block';
        } else {
            customStartDateGroup.style.display = 'none';
            customEndDateGroup.style.display = 'none';
        }
        loadDashboardData();
    });

    startDateInput.addEventListener('change', () => {
        if (dateRangePresetSelect.value === 'custom') loadDashboardData();
    });
    endDateInput.addEventListener('change', () => {
        if (dateRangePresetSelect.value === 'custom') loadDashboardData();
    });
}


// Initialize page on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    theme.loadSavedTheme(); // Apply saved theme
    setupEventListeners();

    // Set default dates for custom input
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 29); // For "30d" preset
    startDateInput.value = formatDate(thirtyDaysAgo);
    endDateInput.value = formatDate(today);

    loadDashboardData();
});
