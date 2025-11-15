
// Handles all communication with the backend API

// Helper to get auth headers
function getAuthHeaders() {
    const accessToken = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json' };
    if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
    }
    return headers;
}

// Generic fetch wrapper
async function post(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An API error occurred');
    }
    return response.json();
}

// --- Auth APIs ---
export async function registerUser(username, password) {
    return post('/register', { username, password });
}

export async function loginUser(username, password) {
    const form_data = new URLSearchParams();
    form_data.append('username', username);
    form_data.append('password', password);

    const response = await fetch('/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form_data
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
    }
    return response.json();
}

export async function loginGoogle(firebaseToken) {
    return post('/token/google', { token: firebaseToken });
}

// --- Portfolio APIs ---
export async function savePortfolio(name, content) {
    return post('/save_portfolio', { name, content });
}

export async function listPortfolios() {
    const response = await fetch('/list_portfolios', { headers: getAuthHeaders() });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to list portfolios');
    }
    return response.json();
}

export async function loadPortfolio(id) {
    const response = await fetch(`/load_portfolio/${id}`, { headers: getAuthHeaders() });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load portfolio');
    }
    return response.json();
}

export async function deletePortfolio(id) {
    const response = await fetch(`/delete_portfolio/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete portfolio');
    }
    return response.json();
}

// --- ETF Data APIs ---
export async function getEtfList() {
    const response = await fetch('/etfs/list');
    return response.json();
}

export async function getRiskFreeRate() {
    const response = await fetch('/etfs/risk_free_rate');
    return response.json();
}

export async function getMapData(tickers, period) {
    const queryParams = new URLSearchParams();
    tickers.forEach(ticker => queryParams.append('tickers', ticker));
    queryParams.append('period', period);

    // Now only call efficient_frontier, which will return both etf_data and frontier_points
    const response = await fetch(`/portfolio/efficient_frontier?${queryParams.toString()}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'An API error occurred while fetching map data');
    }
    const data = await response.json();
    return { etfData: data.etf_data, frontierData: { frontier_points: data.frontier_points, tangency_portfolio: data.tangency_portfolio, tangency_portfolio_weights: data.tangency_portfolio_weights } };
}

export async function getCustomPortfolioData(tickers, weights, period) {
    return post('/portfolio/custom_metrics', { tickers, weights, period });
}

export async function optimizePortfolio(url, tickers, target_value, period) {
    return post(url, { tickers, target_value, period });
}

export async function getHistoricalPerformance(tickers, period) {
    return post('/analysis/historical_performance', { tickers, period });
}

export async function runMonteCarlo(tickers, period, num_simulations, simulation_days) {
    return post('/simulation/monte_carlo', { tickers, period, num_simulations, simulation_days });
}

export async function runDcaSimulation(tickers, weights, period, investment_amount, frequency) {
    return post('/simulation/historical_dca', { tickers, weights, period, investment_amount, frequency });
}

export async function analyzeCsv(csv_data) {
    return post('/analysis/csv', { csv_data });
}

export async function runFutureDcaSimulation(portfolioReturn, portfolioRisk, investmentAmount, frequency, years) {
    return post('/simulation/future_dca', { 
        portfolio_return: portfolioReturn, 
        portfolio_risk: portfolioRisk, 
        investment_amount: investmentAmount, 
        frequency: frequency, 
        years: years 
    });
}

export async function getCorrelationMatrix(tickers, period) {
    return post('/analysis/correlation_matrix', { tickers, period });
}

export async function getEtfDetails(ticker) {
    const response = await fetch(`/etfs/details/${ticker}`);
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch ETF details');
    }
    return response.json();
}
