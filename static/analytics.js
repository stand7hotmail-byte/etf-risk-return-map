// -*- coding: utf-8 -*-
/**
 * Analytics utility module for Google Analytics 4 (GA4) and internal tracking.
 */

import * as api from './api.js'; // Assuming api.js provides fetch wrappers for internal tracking

/**
 * Tracks an affiliate click event and sends data to GA4.
 * Also sends an internal tracking request to the backend.
 *
 * @param {object} broker - The broker object with details like id, broker_name, region, commission_rate.
 * @param {string} placement - The placement of the affiliate link (e.g., "portfolio_result", "broker_page").
 * @param {object | null} portfolioData - Optional: The portfolio context data (tickers, weights) at the time of click.
 * @returns {Promise<object>} The response from the internal tracking API.
 */
export async function trackAffiliateClick(broker, placement, portfolioData = null) {
    // Internal Tracking (using the existing API endpoint)
    let internalTrackingResponse = {};
    try {
        internalTrackingResponse = await api.post('/api/brokers/track-click', {
            broker_id: broker.id,
            placement: placement,
            portfolio_data: portfolioData
        });
    } catch (error) {
        console.error('Error sending internal affiliate click tracking:', error);
        // Continue to GA4 tracking even if internal tracking fails
    }

    // Google Analytics 4 Tracking
    if (typeof gtag !== 'undefined') {
        gtag('event', 'affiliate_click', {
            'broker_id': broker.id,
            'broker_name': broker.broker_name,
            'broker_display_name': broker.display_name,
            'broker_region': broker.region,
            'placement': placement,
            'commission_rate': broker.commission_rate,
            'event_category': 'affiliate_engagement',
            'event_label': `${broker.display_name}_${placement}`,
            'value': broker.commission_rate, // Use commission rate as event value
            'currency': broker.region === 'JP' ? 'JPY' : 'USD' // Set currency based on region
        });
    }

    return internalTrackingResponse;
}

/**
 * Tracks a portfolio creation event and sends data to GA4.
 *
 * @param {string[]} tickers - Array of ETF tickers in the created portfolio.
 * @param {number} numTickers - Number of ETFs in the created portfolio.
 */
export function trackPortfolioCreation(tickers, numTickers) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'portfolio_created', {
            'num_etfs': numTickers,
            'etf_tickers': tickers.join(','),
            'event_category': 'engagement',
            'event_label': 'portfolio_analysis_complete'
        });
    }
}

/**
 * Tracks a page view event and sends data to GA4.
 * This can be used for single-page applications or specific route changes.
 *
 * @param {string} pageTitle - The title of the page being viewed.
 * @param {string} pageLocation - The URL of the page being viewed.
 */
export function trackPageView(pageTitle, pageLocation = window.location.href) {
    if (typeof gtag !== 'undefined') {
        gtag('event', 'page_view', {
            'page_title': pageTitle,
            'page_location': pageLocation
        });
    }
}

// --- Privacy Considerations ---
// In a production environment, you would typically implement a cookie consent banner
// and provide an opt-out mechanism for analytics tracking (e.g., if user declines,
// do not load gtag.js or call gtag functions).
// This basic implementation assumes consent is given or not required for demonstration.
