
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
    const response = await fetch('/etf_list');
    return response.json();
}

export async function getRiskFreeRate() {
    const response = await fetch('/risk_free_rate');
    return response.json();
}

export async function getMapData(tickers, period, constraints) {
    const queryParams = new URLSearchParams();
    tickers.forEach(ticker => queryParams.append('tickers', ticker));
    queryParams.append('period', period);
    queryParams.append('constraints', JSON.stringify(constraints));

    const [etfData, frontierData] = await Promise.all([
        fetch(`/data?${queryParams.toString()}`).then(res => res.json()),
        fetch(`/efficient_frontier?${queryParams.toString()}`).then(res => res.json())
    ]);
    return { etfData, frontierData };
}

export async function getCustomPortfolioData(tickers, weights, period) {
    return post('/custom_portfolio_data', { tickers, weights, period });
}

export async function optimizePortfolio(url, tickers, target_value, period, constraints) {
    return post(url, { tickers, target_value, period, constraints });
}

export async function getHistoricalPerformance(tickers, period) {
    return post('/historical_performance', { tickers, period });
}

export async function runMonteCarlo(tickers, period, num_simulations, simulation_days) {
    return post('/monte_carlo_simulation', { tickers, period, num_simulations, simulation_days });
}

export async function runDcaSimulation(tickers, weights, period, investment_amount, frequency) {
    return post('/dca_simulation', { tickers, weights, period, investment_amount, frequency });
}

export async function analyzeCsv(csv_data) {
    return post('/analyze_csv_data', { csv_data });
}

export async function runFutureDcaSimulation(portfolioReturn, portfolioRisk, investmentAmount, frequency, years) {
    return post('/future_dca_simulation', { 
        portfolio_return: portfolioReturn, 
        portfolio_risk: portfolioRisk, 
        investment_amount: investmentAmount, 
        frequency: frequency, 
        years: years 
    });
}
