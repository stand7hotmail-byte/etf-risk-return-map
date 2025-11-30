import { getCurrentTheme } from './theme.js';

// Handles all UI updates and DOM manipulation not related to auth

// --- DOM Element Exports ---
export const etfCheckboxesDiv = document.getElementById('etf-checkboxes');
export const assetClassFilter = document.getElementById('asset-class-filter');
export const regionFilter = document.getElementById('region-filter');
export const styleFilter = document.getElementById('style-filter');
export const sizeFilter = document.getElementById('size-filter');
export const sectorFilter = document.getElementById('sector-filter');
export const themeFilter = document.getElementById('theme-filter');
export const selectAllBtn = document.getElementById('select-all-btn');
export const deselectAllBtn = document.getElementById('deselect-all-btn');

export const generateMapBtn = document.getElementById('generate-map-btn');
export const dataPeriodSelect = document.getElementById('data-period-select');
export const compositionDetailsDiv = document.getElementById('composition-details');
export const portfolioSlidersDiv = document.getElementById('portfolio-sliders');
export const calculateCustomPortfolioBtn = document.getElementById('calculate-custom-portfolio-btn');
export const customPortfolioResultDiv = document.getElementById('custom-portfolio-result');
export const targetReturnInput = document.getElementById('target-return-input');
export const optimizeByReturnBtn = document.getElementById('optimize-by-return-btn');
export const targetRiskInput = document.getElementById('target-risk-input');
export const optimizeByRiskBtn = document.getElementById('optimize-by-risk-btn');
export const targetOptimizationResultDiv = document.getElementById('target-optimization-result');
export const showHistoricalPerformanceBtn = document.getElementById('show-historical-performance-btn');
export const historicalPerformanceGraphDiv = document.getElementById('historical-performance-graph');
export const showCorrelationMatrixBtn = document.getElementById('show-correlation-matrix-btn');
export const correlationMatrixGraphDiv = document.getElementById('correlation-matrix-graph');
export const numSimulationsInput = document.getElementById('num-simulations-input');
export const simulationDaysInput = document.getElementById('simulation-days-input');
export const runMonteCarloBtn = document.getElementById('run-monte-carlo-btn');
export const monteCarloGraphDiv = document.getElementById('monte-carlo-graph');
export const monteCarloResultsDiv = document.getElementById('monte-carlo-results');
export const csvFileInput = document.getElementById('csv-file-input');
export const analyzeCsvBtn = document.getElementById('analyze-csv-btn');
export const csvAnalysisResultsDiv = document.getElementById('csv-analysis-results');
export const csvAnalysisGraphDiv = document.getElementById('csv-analysis-graph');
export const dcaAmountInput = document.getElementById('dca-amount-input');
export const dcaFrequencySelect = document.getElementById('dca-frequency-select');
export const runDcaSimulationBtn = document.getElementById('run-dca-simulation-btn');
export const dcaSimulationGraphDiv = document.getElementById('dca-simulation-graph');
export const dcaSimulationResultsDiv = document.getElementById('dca-simulation-results');
export const dcaYearsInput = document.getElementById('dca-years-input');
export const portfolioNameInput = document.getElementById('portfolio-name-input');
export const savePortfolioBtn = document.getElementById('save-portfolio-btn');
export const listPortfoliosBtn = document.getElementById('list-portfolios-btn');
export const savedPortfoliosSelect = document.getElementById('saved-portfolios-select');
export const loadPortfolioBtn = document.getElementById('load-portfolio-btn');
export const deletePortfolioBtn = document.getElementById('delete-portfolio-btn');
export const portfolioMessageDiv = document.getElementById('portfolio-message');
export const recommendedBrokersList = document.getElementById('recommended-brokers-list');

// --- UI Functions ---

/**
 * Creates an HTML element for a single broker card for the recommendation section.
 * @param {object} broker - Broker data.
 * @returns {HTMLElement} - The created card element.
 */
function createBrokerCard(broker) {
    const card = document.createElement('div');
    card.className = 'col-md-4 mb-3 d-flex'; // Use flexbox for equal height cards

    card.innerHTML = `
        <div class="card h-100">
            <div class="card-body d-flex flex-column">
                <h6 class="card-title">${broker.display_name}</h6>
                <div class="mb-2">
                    ${JSON.parse(broker.pros).slice(0, 2).map(p => `<span class="badge bg-secondary-subtle text-secondary me-1 mb-1">${p}</span>`).join('')}
                </div>
                <p class="card-text small flex-grow-1"><strong>最適な人:</strong> ${broker.best_for}</p>
                <a href="#" class="btn btn-sm btn-outline-primary mt-auto affiliate-link"
                   data-broker-id="${broker.id}" data-placement="portfolio_recommendation">
                    詳細を見る
                    <span class="badge bg-info ms-1">AD</span>
                </a>
            </div>
        </div>
    `;

    // Note: The event listener for tracking clicks will be attached in main.js
    // to have access to the portfolio data context.
    return card;
}


/**
 * Renders the recommended brokers into the recommendation section.
 * @param {Array} brokers - An array of broker objects to display.
 */
export function displayBrokerRecommendations(brokers) {
    if (!recommendedBrokersList) return;

    recommendedBrokersList.innerHTML = '';
    const recommendationContainer = document.getElementById('broker-recommendation');

    if (brokers.length > 0) {
        brokers.slice(0, 3).forEach(broker => {
            const card = createBrokerCard(broker);
            recommendedBrokersList.appendChild(card);
        });
        recommendationContainer.style.display = 'block';

        // Add a fade-in animation
        recommendationContainer.classList.add('fade-in');
        setTimeout(() => recommendationContainer.classList.remove('fade-in'), 500);
    } else {
        recommendationContainer.style.display = 'none';
    }
}


export function createEtfCheckboxes(etfList, definitions, container, currentlyChecked) {
    container.innerHTML = '';
    if (etfList.length === 0) {
        container.innerHTML = '<p class="text-muted">No ETFs match your filter.</p>';
        return;
    }
    etfList.forEach(ticker => {
        const etfInfo = definitions[ticker];
        const div = document.createElement('div');
        div.className = 'form-check d-flex align-items-center';

        const checkbox = document.createElement('input');
        checkbox.className = 'form-check-input';
        checkbox.type = 'checkbox';
        checkbox.value = ticker;
        checkbox.id = `checkbox-${ticker}`;
        checkbox.checked = currentlyChecked.has(ticker);

        const label = document.createElement('label');
        label.className = 'form-check-label me-2';
        label.setAttribute('for', `checkbox-${ticker}`);
        label.textContent = ticker;

        const popoverTrigger = document.createElement('span');
        popoverTrigger.className = 'badge bg-light text-dark rounded-pill ms-auto'; // Use ms-auto to push to the right
        popoverTrigger.style.cursor = 'pointer';
        popoverTrigger.innerHTML = '<i class="bi bi-info-lg"></i>';
        popoverTrigger.setAttribute('tabindex', '0'); // Make it focusable
        popoverTrigger.setAttribute('role', 'button'); // Accessibility
        popoverTrigger.setAttribute('data-bs-toggle', 'popover');
        popoverTrigger.setAttribute('data-bs-trigger', 'focus'); // Changed to focus
        popoverTrigger.setAttribute('data-bs-title', etfInfo.name || ticker);
        popoverTrigger.setAttribute('data-ticker', ticker); // Add ticker data attribute
        popoverTrigger.setAttribute('data-bs-content', 'Loading...'); // Default content
        popoverTrigger.setAttribute('data-bs-html', 'true');

        div.appendChild(checkbox);
        div.appendChild(label);
        div.appendChild(popoverTrigger);
        container.appendChild(div);
    });
}

export function createPortfolioSliders(tickers, container, weightsVar) {
    container.innerHTML = ''; // Clear existing sliders
    const initialWeight = tickers.length > 0 ? 100 / tickers.length : 0;
    weightsVar = {}; // Reset weights object

    tickers.forEach(ticker => {
        const sliderContainer = document.createElement('div');
        sliderContainer.className = 'mb-3';

        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = `${ticker}: `;
        
        const weightSpan = document.createElement('span');
        weightSpan.id = `${ticker}-weight`;
        weightSpan.className = 'fw-bold';
        weightSpan.textContent = `${initialWeight.toFixed(2)}%`;
        
        label.appendChild(weightSpan);

        const slider = document.createElement('input');
        slider.className = 'form-range';
        slider.type = 'range';
        slider.min = 0;
        slider.max = 100;
        slider.value = initialWeight;
        slider.step = 0.01;
        slider.dataset.ticker = ticker;

        sliderContainer.appendChild(label);
        sliderContainer.appendChild(slider);
        container.appendChild(sliderContainer);
        
        weightsVar[ticker] = initialWeight;
    });
    return weightsVar;
}

export function updateSliderPercentage(ticker, value) {
    const weightSpan = document.getElementById(`${ticker}-weight`);
    if (weightSpan) {
        weightSpan.textContent = `${parseFloat(value).toFixed(2)}%`;
    }
}


export function populatePortfolioList(portfolios) {
    savedPortfoliosSelect.innerHTML = '';
    if (portfolios.length === 0) {
        savedPortfoliosSelect.innerHTML = '<option value="">No portfolios saved</option>';
        loadPortfolioBtn.disabled = true;
        deletePortfolioBtn.disabled = true;
    } else {
        portfolios.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = `${p.name} (ID: ${p.id})`;
            savedPortfoliosSelect.appendChild(option);
        });
        loadPortfolioBtn.disabled = false;
        deletePortfolioBtn.disabled = false;
    }
}

export function displayMessage(element, message, isError = false) {
    element.style.color = isError ? 'red' : 'green';
    element.textContent = message;
}

export function displayPortfolioComposition(weights) {
    compositionDetailsDiv.innerHTML = ''; // Clear previous content
    const title = document.createElement('h5');
    title.className = 'card-title';
    title.textContent = 'Max Sharpe Ratio Portfolio Composition';
    compositionDetailsDiv.appendChild(title);

    if (Object.keys(weights).length > 0) {
        let tableHtml = '<table class="table table-striped table-hover table-sm mt-3"><thead><tr><th>ETF Ticker</th><th>Weight</th></tr></thead><tbody>';
        for (const ticker in weights) {
            tableHtml += `<tr><td>${ticker}</td><td>${(weights[ticker] * 100).toFixed(2)}%</td></tr>`;
        }
        tableHtml += '</tbody></table>';
        compositionDetailsDiv.innerHTML += tableHtml;
    } else {
        compositionDetailsDiv.innerHTML += '<p class="text-muted mt-3">Could not calculate Max Sharpe Ratio Portfolio composition.</p>';
    }
}

export function drawMap(traces, layout) {
    const currentTheme = getCurrentTheme();
    layout.template = currentTheme === 'dark' ? 'plotly_dark' : 'plotly';
    Plotly.newPlot('graph', traces, layout);
}

export function addTrace(traceData) {
    const graphDiv = document.getElementById('graph');
    const currentData = graphDiv.data || [];
    const updatedData = currentData.filter(trace => trace.name !== traceData.name);
    updatedData.push(traceData);
    Plotly.react('graph', updatedData, graphDiv.layout);
}

export function clearGraph(graphId) {
    Plotly.purge(graphId);
}

export function drawCorrelationHeatmap(data, containerId) {
    const trace = {
        x: data.x,
        y: data.y,
        z: data.z,
        type: 'heatmap',
        colorscale: 'Viridis',
        zmin: -1,
        zmax: 1
    };

    const currentTheme = getCurrentTheme(); // Get current theme
    const layout = {
        title: 'Correlation Matrix',
        xaxis: { automargin: true },
        yaxis: { automargin: true },
        template: currentTheme === 'dark' ? 'plotly_dark' : 'plotly' // Apply theme
    };

    Plotly.newPlot(containerId, [trace], layout);
}

export function populateFilterOptions(selectElement, options) {
    const selectedValue = selectElement.value;
    while (selectElement.options.length > 1) {
        selectElement.remove(1);
    }
    options.forEach(optionValue => {
        const option = document.createElement('option');
        option.value = optionValue;
        option.textContent = optionValue;
        selectElement.appendChild(option);
    });
    selectElement.value = selectedValue;
}