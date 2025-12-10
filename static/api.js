// -*- coding: utf-8 -*-
/**
 * API utility module for making authenticated and unauthenticated requests.
 */

// Base URL for the API (assuming it's on the same host)
const API_BASE_URL = ''; // Relative path, e.g., /api

/**
 * Handles HTTP responses, checking for errors.
 * @param {Response} response - The fetch API response object.
 * @returns {Promise<any>} - The JSON response data.
 * @throws {Error} If the response is not OK.
 */
async function handleResponse(response) {
    console.log('handleResponse called. response.ok:', response.ok, 'response.status:', response.status); // Debug log

    if (!response.ok) {
        let errorData = {};
        try {
            errorData = await response.json(); // Try to parse error body if available
        } catch (e) {
            console.warn('Could not parse error response JSON:', e);
        }
        const errorMessage = errorData.detail || response.statusText;
        throw new Error(`API Error: ${response.status} - ${errorMessage}`);
    }
    
    let jsonData;
    try {
        jsonData = await response.json();
        console.log('handleResponse: Successfully parsed JSON data.', jsonData); // Debug log
        return jsonData;
    } catch (e) {
        console.error('handleResponse: Error parsing JSON response:', e); // Debug log for parsing errors
        throw new Error(`API Error: Failed to parse JSON response - ${e.message}`);
    }
}

/**
 * Fetches data from the API.
 * @param {string} endpoint - The API endpoint (e.g., "/api/brokers").
 * @param {object} params - Query parameters.
 * @param {string} [token] - Optional JWT token for authenticated requests.
 * @returns {Promise<any>} - The JSON response data.
 */
export async function get(endpoint, params = {}, token = null) {
    const url = new URL(`${API_BASE_URL}${endpoint}`, window.location.origin);
    Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
            if (Array.isArray(params[key])) {
                params[key].forEach(item => url.searchParams.append(key, item));
            } else {
                url.searchParams.append(key, params[key]);
            }
        }
    });

    console.log('API GET request:', url.toString()); // Debug log

    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url.toString(), {
        method: 'GET',
        headers: headers,
    });
    return handleResponse(response);
}

/**
 * Posts data to the API.
 * @param {string} endpoint - The API endpoint.
 * @param {object} data - The data to send in the request body.
 * @param {string} [token] - Optional JWT token.
 * @returns {Promise<any>} - The JSON response data.
 */
export async function post(endpoint, data = {}, token = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data),
    });
    return handleResponse(response);
}

/**
 * Puts data to the API.
 * @param {string} endpoint - The API endpoint.
 * @param {object} data - The data to send in the request body.
 * @param {string} [token] - Optional JWT token.
 * @returns {Promise<any>} - The JSON response data.
 */
export async function put(endpoint, data = {}, token = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: headers,
        body: JSON.stringify(data),
    });
    return handleResponse(response);
}

/**
 * Deletes data via the API.
 * @param {string} endpoint - The API endpoint.
 * @param {string} [token] - Optional JWT token.
 * @returns {Promise<any>} - The JSON response data.
 */
export async function del(endpoint, token = null) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        headers: headers,
    });
    return handleResponse(response);
}

/**
 * Fetches the list of ETFs from the backend.
 * @returns {Promise<Array>} - A promise that resolves to an array of ETF objects.
 */
export async function getEtfList() {
    return get('/etfs/list');
}

/**
 * Fetches ETF map data (efficient frontier, ETF data) from the backend.
 * @param {string[]} tickers - Array of ETF tickers.
 * @param {string} period - Data period (e.g., "5y").
 * @returns {Promise<object>} - A promise that resolves to an object containing etfData and frontierData.
 */
export async function getMapData(tickers, period) {
    return get('/portfolio/efficient_frontier', { tickers, period });
}

/**
 * Fetches the risk-free rate from the backend.
 * @returns {Promise<object>} - A promise that resolves to an object containing the risk_free_rate.
 */
export async function getRiskFreeRate() {
    return get('/etfs/risk_free_rate');
}