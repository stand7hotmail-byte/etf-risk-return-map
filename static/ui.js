
// Handles all UI updates and DOM manipulation not related to auth

// --- DOM Element Exports ---
export const etfCheckboxesDiv = document.getElementById('etf-checkboxes');
export const assetClassFilter = document.getElementById('asset-class-filter');
export const regionFilter = document.getElementById('region-filter');
export const constraintInputsDiv = document.getElementById('constraint-inputs');
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

// --- UI Functions ---

export function createEtfCheckboxes(etfList, definitions, container) {
    container.innerHTML = '';
    etfList.forEach(ticker => {
        const etfInfo = definitions[ticker];
        const label = document.createElement('label');
        label.title = etfInfo ? etfInfo.name : 'No description'; // Add tooltip
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = ticker;
        checkbox.checked = true; // Default to all selected
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(ticker));
        container.appendChild(label);
    });
}

export function createPortfolioSliders(tickers, container, weightsVar) {
    container.innerHTML = ''; // Clear existing sliders
    const initialWeight = 100 / tickers.length;
    weightsVar = {}; // Reset weights object

    tickers.forEach(ticker => {
        const sliderContainer = document.createElement('div');
        sliderContainer.style.marginBottom = '10px';
        sliderContainer.innerHTML = `
            <label>${ticker}: <span id="${ticker}-weight">${initialWeight.toFixed(2)}%</span></label>
            <input type="range" min="0" max="100" value="${initialWeight}" step="0.01" data-ticker="${ticker}" style="width: 100%;">
        `;
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

export function createConstraintInputs(tickers, container) {
    container.innerHTML = '';
    const constraints = {};
    tickers.forEach(ticker => {
        const constraintRow = document.createElement('div');
        constraintRow.style.marginBottom = '5px';
        constraintRow.innerHTML = `
            <label>${ticker}:</label>
            Min: <input type="number" class="constraint-min" data-ticker="${ticker}" value="0" min="0" max="100" step="0.01" style="width: 60px;">
            Max: <input type="number" class="constraint-max" data-ticker="${ticker}" value="100" min="0" max="100" step="0.01" style="width: 60px;">
        `;
        container.appendChild(constraintRow);
        constraints[ticker] = { min: 0, max: 100 };
    });
    return constraints;
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
    if (Object.keys(weights).length > 0) {
        let compositionHtml = '<table><thead><tr><th>ETF Ticker</th><th>Weight</th></tr></thead><tbody>';
        for (const ticker in weights) {
            compositionHtml += `<tr><td>${ticker}</td><td>${(weights[ticker] * 100).toFixed(2)}%</td></tr>`;
        }
        compositionHtml += '</tbody></table>';
        compositionDetailsDiv.innerHTML = compositionHtml;
    } else {
        compositionDetailsDiv.innerHTML = 'Could not calculate Max Sharpe Ratio Portfolio composition.';
    }
}

export function drawMap(traces, layout) {
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
