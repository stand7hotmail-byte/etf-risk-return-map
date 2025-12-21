// -*- coding: utf-8 -*-
/**
 * JavaScript module for the broker comparison page.
 * Handles fetching broker data, dynamic rendering, filtering, sorting, and affiliate click tracking.
 */

import * as api from './api.js'; // Assuming api.js provides fetch wrappers
import * as theme from './theme.js'; // For theme-related functionalities
// import * as analytics from './analytics.js'; // analytics.jsの代わりに新しい関数を実装

// DOM Elements
const brokerCardsContainer = document.getElementById('broker-cards-container');
const comparisonTableBody = document.getElementById('comparison-table-body');
const regionTabsContainer = document.getElementById('regionTabs');
const loadingSpinner = document.getElementById('loading-spinner');
const brokerComparisonTable = document.getElementById('broker-comparison-table');

let allBrokers = []; // Stores all fetched brokers

async function handleAffiliateClick(event, broker, placement) {
    event.preventDefault();

    console.log('[Brokers] Affiliate link clicked:', {
        broker: broker.broker_name,
        placement: placement,
        url: broker.affiliate_url
    });

    const trackingData = {
        broker_id: broker.broker_id,
        placement: placement,
        portfolio_data: null
    };

    console.log('[Brokers] Sending tracking request:', trackingData);

    const timeoutPromise = new Promise((resolve) => {
        setTimeout(() => {
            console.log('[Brokers] Tracking API timeout (2s), proceeding to redirect');
            resolve({ timeout: true });
        }, 2000);
    });

    const trackingPromise = fetch('/api/brokers/track-click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(trackingData)
    })
    .then(response => {
        console.log('[Brokers] Tracking API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('[Brokers] Tracking API success:', data);
        return { success: true, data };
    })
    .catch(error => {
        console.error('[Brokers] Tracking API error:', error);
        return { success: false, error: error.message };
    });

    const result = await Promise.race([trackingPromise, timeoutPromise]);

    if (result.timeout) {
        console.warn('[Brokers] Proceeding without tracking confirmation');
    } else if (result.success) {
        console.log('[Brokers] Tracking recorded successfully');
    } else {
        console.error('[Brokers] Tracking failed:', result.error);
    }

    if (typeof gtag !== 'undefined') {
        console.log('[Brokers] Sending GA4 event');
        gtag('event', 'affiliate_click', {
            'broker_name': broker.broker_name,
            'broker_region': broker.region,
            'placement': placement,
            'event_category': 'affiliate'
        });
    }

    console.log('[Brokers] Opening affiliate URL in new tab:', broker.affiliate_url);
    window.open(broker.affiliate_url, '_blank', 'noopener,noreferrer');
}

function generateStarRating(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    let stars = '';
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="bi bi-star-fill text-warning"></i>';
    }
    if (hasHalfStar) {
        stars += '<i class="bi bi-star-half text-warning"></i>';
    }
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="bi bi-star text-warning"></i>';
    }

    return stars;
}


function createBrokerCard(broker, placement = 'broker_page') {
    const card = document.createElement('div');
    card.className = 'col-md-4 mb-4';

    let pros = [];
    try {
        pros = typeof broker.pros === 'string' ? JSON.parse(broker.pros) : broker.pros || [];
    } catch (e) {
        console.error('[Brokers] Failed to parse pros:', e);
        pros = [];
    }

    const stars = generateStarRating(broker.rating || 0);

    card.innerHTML = `
        <div class="card h-100 shadow-sm">
            ${broker.logo_url ? `
                <img src="${broker.logo_url}" class="card-img-top p-3" alt="${broker.display_name}" style="height: 80px; object-fit: contain;">
            ` : ''}
            <div class="card-body d-flex flex-column">
                <h5 class="card-title">${broker.display_name}</h5>
                <div class="mb-2">
                    ${stars}
                    <small class="text-muted ms-2">(${broker.rating || 0})</small>
                </div>
                <p class="card-text text-muted small">${broker.description || ''}</p>

                <div class="mb-3">
                    <h6 class="text-success mb-2">主なメリット</h6>
                    <ul class="small ps-3">
                        ${pros.map(pro => `<li>${pro}</li>`).join('')}
                    </ul>
                </div>

                <div class="mb-3">
                    <strong class="small">最適な人:</strong>
                    <span class="badge bg-info text-dark">${broker.best_for || ''}</span>
                </div>

                <div class="mt-auto">
                    <button class="btn btn-primary w-100 affiliate-link-btn"
                            data-broker-id="${broker.id}"
                            data-broker-name="${broker.broker_name}"
                            data-affiliate-url="${broker.affiliate_url}">
                        公式サイトで口座開設（無料）
                        <span class="badge bg-light text-dark ms-2">AD</span>
                    </button>
                </div>
            </div>
        </div>
    `;

    const button = card.querySelector('.affiliate-link-btn');
    button.addEventListener('click', (e) => {
        const brokerData = {
            broker_id: parseInt(button.dataset.brokerId),
            broker_name: button.dataset.brokerName,
            display_name: broker.display_name,
            region: broker.region,
            affiliate_url: button.dataset.affiliateUrl
        };
        handleAffiliateClick(e, brokerData, placement);
    });

    return card;
}


async function loadBrokers(region = 'all') {
    console.log('[Brokers] Loading brokers for region:', region);

    const container = document.getElementById('broker-cards-container');
    if (!container) {
        console.error('[Brokers] Container #broker-cards-container not found');
        return;
    }

    container.innerHTML = '<div class="text-center py-5"><div class="spinner-border" role="status"></div></div>';

    try {
        const url = region === 'all'
            ? '/api/brokers'
            : `/api/brokers?region=${region}`;

        console.log('[Brokers] Fetching from:', url);

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        const brokers = data || []; // `data`が直接配列であることを期待

        if (brokers.length === 0) {
            container.innerHTML = '<div class="col-12 text-center py-5"><p class="text-muted">この地域の証券会社は見つかりませんでした。</p></div>';
            return;
        }

        container.innerHTML = '';
        brokers.forEach(broker => {
            const card = createBrokerCard(broker, 'broker_page');
            container.appendChild(card);
        });

        console.log('[Brokers] Brokers displayed successfully');

    } catch (error) {
        console.error('[Brokers] Error loading brokers:', error);
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger" role="alert">
                    <h4 class="alert-heading">エラー</h4>
                    <p>証券会社情報の取得に失敗しました: ${error.message}</p>
                    <button class="btn btn-primary" onclick="loadBrokers('${region}')">再試行</button>
                </div>
            </div>
        `;
    }
}


function filterByRegion(region) {
    console.log('[Brokers] Filtering by region:', region);

    document.querySelectorAll('.region-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.region === region) {
            tab.classList.add('active');
        }
    });

    loadBrokers(region);
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[Brokers] Page initializing...');

    document.querySelectorAll('.region-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const region = tab.dataset.region;
            filterByRegion(region);
        });
    });

    try {
        loadBrokers('US');
    } catch (error) {
        console.error('[Brokers] Initial loadBrokers failed:', error);
    }

    console.log('[Brokers] Page initialized');
});