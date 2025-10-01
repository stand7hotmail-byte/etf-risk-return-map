import * as api from './api.js';
import * as ui from './ui.js';
import { initAuth } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {

    let currentWeights = {};

    let etfDefinitions = {}; // To store ETF metadata

    // Initialize authentication
    initAuth();

    const etfSearchInput = document.getElementById('etf-search-input');

    // --- Event Listeners ---
    ui.assetClassFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.regionFilter.addEventListener('change', () => filterAndDisplayEtfs());
    etfSearchInput.addEventListener('input', () => filterAndDisplayEtfs());

    function filterAndDisplayEtfs() {
        // Check if the checkbox container has been populated before.
        const isInitialLoad = ui.etfCheckboxesDiv.children.length === 0;

        let currentlyChecked;
        if (!isInitialLoad) {
            currentlyChecked = new Set(
                Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                     .map(cb => cb.value)
            );
        } else {
            currentlyChecked = new Set(Object.keys(etfDefinitions));
        }

        const assetClass = ui.assetClassFilter.value;
        const region = ui.regionFilter.value;
        const searchTerm = etfSearchInput.value.normalize('NFKC').toLowerCase();

        const filteredEtfs = Object.keys(etfDefinitions).filter(ticker => {
            const etf = etfDefinitions[ticker];
            if (!etf) return false; // Safety check

            const assetMatch = assetClass === 'all' || etf.asset_class === assetClass;
            const regionMatch = region === 'all' || etf.region === region;
            const searchMatch = searchTerm === '' || 
                                ticker.toLowerCase().includes(searchTerm) || 
                                (etf.name && etf.name.toLowerCase().includes(searchTerm)); // Safety check for name
            return assetMatch && regionMatch && searchMatch;
        });

        // Pass the set of checked tickers to the UI function.
        ui.createEtfCheckboxes(filteredEtfs, etfDefinitions, ui.etfCheckboxesDiv, currentlyChecked);
    }

    // --- Main Application Logic ---

    async function generateMap(callback) {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length > 20) {
            alert("Please select 20 or fewer ETFs for analysis.");
            return;
        }

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF.');
            ui.clearGraph('graph');
            ui.compositionDetailsDiv.innerHTML = 'Select ETFs and click \'Generate Map\' to see composition.';
            ui.portfolioSlidersDiv.innerHTML = '';
            ui.customPortfolioResultDiv.innerHTML = '';
            return;
        }

        // Create UI components and get initial values
        currentWeights = ui.createPortfolioSliders(selectedTickers, ui.portfolioSlidersDiv, currentWeights);
        ui.customPortfolioResultDiv.innerHTML = '';

        const period = ui.dataPeriodSelect.value;

        try {
            const { etfData, frontierData } = await api.getMapData(selectedTickers, period);
            const riskFreeRateData = await api.getRiskFreeRate();
            
            if (frontierData.error) {
                alert(frontierData.error);
                return;
            }

            const traces = [];
            // Add ETF trace
            traces.push({
                x: etfData.map(item => item.Risk),
                y: etfData.map(item => item.Return),
                mode: 'markers+text', type: 'scatter', name: 'ETFs',
                text: etfData.map(item => item.Ticker), textposition: 'top center',
                marker: { size: 12 }
            });

            // Add Efficient Frontier trace
            traces.push({
                x: frontierData.frontier_points.map(item => item.Risk),
                y: frontierData.frontier_points.map(item => item.Return),
                mode: 'lines', type: 'scatter', name: 'Efficient Frontier',
                line: { color: 'blue', width: 2, shape: 'spline' } // Use spline for smoothing
            });

            // Add Risk-Free Rate trace
            const riskFreeRate = riskFreeRateData.risk_free_rate;
            traces.push({ x: [0], y: [riskFreeRate], mode: 'markers', type: 'scatter', name: 'Risk-Free Rate', marker: { size: 20, color: 'green', symbol: 'star' } });

            const tangencyPortfolio = frontierData.tangency_portfolio;
            if (tangencyPortfolio) {
                // Add CML trace
                traces.push({ x: [0, tangencyPortfolio.Risk], y: [riskFreeRate, tangencyPortfolio.Return], mode: 'lines', type: 'scatter', name: 'Capital Market Line', line: { color: 'red', width: 2, dash: 'dash' } });
                // Add Max Sharpe Portfolio trace
                traces.push({ x: [tangencyPortfolio.Risk], y: [tangencyPortfolio.Return], mode: 'markers', type: 'scatter', name: 'Max Sharpe Ratio Portfolio', marker: { size: 15, color: 'darkorange', symbol: 'diamond' } });
                ui.displayPortfolioComposition(frontierData.tangency_portfolio_weights);
            } else {
                ui.displayPortfolioComposition({});
            }

            const layout = { title: 'ETF Risk-Return Map (Annualized)', xaxis: { title: 'Risk (Annualized Volatility)' }, yaxis: { title: 'Expected Return (Annualized)' } };
            ui.drawMap(traces, layout);

        } catch (error) {
            console.error('Error generating map:', error);
            alert('Failed to generate map. See console for details.');
        } finally {
            if (callback && typeof callback === 'function') {
                callback();
            }
        }
    }

    async function calculateAndDrawCustomPortfolio() {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length === 0) return;

        let totalWeight = 0;
        const rawWeights = {};
        selectedTickers.forEach(ticker => {
            const slider = ui.portfolioSlidersDiv.querySelector(`input[data-ticker="${ticker}"]`);
            rawWeights[ticker] = slider ? parseFloat(slider.value) : (currentWeights[ticker] || 0);
            totalWeight += rawWeights[ticker];
        });

        if (totalWeight === 0) return;

        const normalizedWeights = {};
        selectedTickers.forEach(ticker => { normalizedWeights[ticker] = (rawWeights[ticker] || 0) / totalWeight; });

        try {
            const customPortfolioData = await api.getCustomPortfolioData(selectedTickers, normalizedWeights, ui.dataPeriodSelect.value);
            ui.customPortfolioResultDiv.innerHTML = `<h3>Your Custom Portfolio</h3><p><strong>Risk:</strong> ${(customPortfolioData.Risk * 100).toFixed(2)}%</p><p><strong>Return:</strong> ${(customPortfolioData.Return * 100).toFixed(2)}%</p>`;
            ui.addTrace({ x: [customPortfolioData.Risk], y: [customPortfolioData.Return], mode: 'markers', type: 'scatter', name: 'Your Custom Portfolio', marker: { size: 15, color: 'purple', symbol: 'star' } });
        } catch (error) {
            console.error('Error calculating custom portfolio:', error);
            ui.customPortfolioResultDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    }

    function applyPortfolioState(state) {
        if (!state || !state.selectedTickers) return;

        ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = state.selectedTickers.includes(cb.value);
        });

        if (state.dataPeriod) ui.dataPeriodSelect.value = state.dataPeriod;

        const postGenerationAction = () => {
            if (state.weights) {
                for (const ticker in state.weights) {
                    const weight = state.weights[ticker];
                    const slider = ui.portfolioSlidersDiv.querySelector(`input[data-ticker="${ticker}"]`);
                    if (slider) {
                        slider.value = weight;
                        ui.updateSliderPercentage(ticker, weight);
                        currentWeights[ticker] = parseFloat(weight);
                    }
                }
                calculateAndDrawCustomPortfolio();
            }
        };
        generateMap(postGenerationAction);
    }

    // --- Event Listeners ---
    ui.generateMapBtn.addEventListener('click', () => generateMap());
    ui.calculateCustomPortfolioBtn.addEventListener('click', calculateAndDrawCustomPortfolio);

    ui.portfolioSlidersDiv.addEventListener('input', (event) => {
        if (event.target.type === 'range') {
            const ticker = event.target.dataset.ticker;
            currentWeights[ticker] = parseFloat(event.target.value);
            ui.updateSliderPercentage(ticker, event.target.value);
        }
    });



    // Portfolio Management Listeners
    ui.savePortfolioBtn.addEventListener('click', async () => {
        const portfolioName = ui.portfolioNameInput.value;
        if (!portfolioName) {
            return ui.displayMessage(ui.portfolioMessageDiv, 'Please enter a portfolio name.', true);
        }
        const portfolioState = {
            selectedTickers: Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value),
            dataPeriod: ui.dataPeriodSelect.value,
            weights: currentWeights
        };
        try {
            const result = await api.savePortfolio(portfolioName, portfolioState);
            ui.displayMessage(ui.portfolioMessageDiv, result.message);
            ui.listPortfoliosBtn.click(); // Refresh list
        } catch (error) {
            ui.displayMessage(ui.portfolioMessageDiv, error.message, true);
        }
    });

    ui.listPortfoliosBtn.addEventListener('click', async () => {
        try {
            const portfolios = await api.listPortfolios();
            ui.populatePortfolioList(portfolios);
            ui.displayMessage(ui.portfolioMessageDiv, 'Portfolios loaded.');
        } catch (error) {
            ui.displayMessage(ui.portfolioMessageDiv, error.message, true);
        }
    });

    ui.loadPortfolioBtn.addEventListener('click', async () => {
        const portfolioId = ui.savedPortfoliosSelect.value;
        if (!portfolioId) {
            return ui.displayMessage(ui.portfolioMessageDiv, 'Please select a portfolio to load.', true);
        }
        try {
            const loadedData = await api.loadPortfolio(portfolioId);
            ui.displayMessage(ui.portfolioMessageDiv, `Portfolio ${portfolioId} loaded. Applying state...`);
            applyPortfolioState(loadedData);
        } catch (error) {
            ui.displayMessage(ui.portfolioMessageDiv, error.message, true);
        }
    });

    ui.deletePortfolioBtn.addEventListener('click', async () => {
        const portfolioId = ui.savedPortfoliosSelect.value;
        if (!portfolioId || !confirm('Are you sure you want to delete this portfolio?')) return;
        try {
            const result = await api.deletePortfolio(portfolioId);
            ui.displayMessage(ui.portfolioMessageDiv, result.message);
            ui.listPortfoliosBtn.click(); // Refresh list
        } catch (error) {
            ui.displayMessage(ui.portfolioMessageDiv, error.message, true);
        }
    });

    ui.optimizeByReturnBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length === 0) return alert('Please select at least one ETF.');
        
        const targetReturn = parseFloat(ui.targetReturnInput.value) / 100;
        if (isNaN(targetReturn) || targetReturn <= 0) return alert('Please enter a valid positive target return.');

        const period = ui.dataPeriodSelect.value;

        try {
            const result = await api.optimizePortfolio('/optimize_by_return', selectedTickers, targetReturn, period);
            
            let resultHtml = `<h3>Optimized for Return</h3>
                <p><strong>Achieved Return:</strong> ${(result.Return * 100).toFixed(2)}%</p>
                <p><strong>Risk:</strong> ${(result.Risk * 100).toFixed(2)}%</p>
                <h4>Composition:</h4>
                <table><thead><tr><th>ETF</th><th>Weight</th></tr></thead><tbody>`;
            for (const ticker in result.weights) {
                resultHtml += `<tr><td>${ticker}</td><td>${(result.weights[ticker] * 100).toFixed(2)}%</td></tr>`;
            }
            resultHtml += '</tbody></table>';
            ui.targetOptimizationResultDiv.innerHTML = resultHtml;

            ui.addTrace({ x: [result.Risk], y: [result.Return], mode: 'markers', type: 'scatter', name: 'Optimized by Return', marker: { size: 15, color: 'blue', symbol: 'circle' } });
        } catch (error) {
            ui.targetOptimizationResultDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    ui.optimizeByRiskBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length === 0) return alert('Please select at least one ETF.');

        const targetRisk = parseFloat(ui.targetRiskInput.value) / 100;
        if (isNaN(targetRisk) || targetRisk <= 0) return alert('Please enter a valid positive target risk.');

        const period = ui.dataPeriodSelect.value;

        try {
            const result = await api.optimizePortfolio('/optimize_by_risk', selectedTickers, targetRisk, period);

            let resultHtml = `<h3>Optimized for Risk</h3>
                <p><strong>Achieved Risk:</strong> ${(result.Risk * 100).toFixed(2)}%</p>
                <p><strong>Return:</strong> ${(result.Return * 100).toFixed(2)}%</p>
                <h4>Composition:</h4>
                <table><thead><tr><th>ETF</th><th>Weight</th></tr></thead><tbody>`;
            for (const ticker in result.weights) {
                resultHtml += `<tr><td>${ticker}</td><td>${(result.weights[ticker] * 100).toFixed(2)}%</td></tr>`;
            }
            resultHtml += '</tbody></table>';
            ui.targetOptimizationResultDiv.innerHTML = resultHtml;

            ui.addTrace({ x: [result.Risk], y: [result.Return], mode: 'markers', type: 'scatter', name: 'Optimized by Risk', marker: { size: 15, color: 'green', symbol: 'square' } });
        } catch (error) {
            ui.targetOptimizationResultDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    ui.showHistoricalPerformanceBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length === 0) return alert('Please select at least one ETF.');
        const period = ui.dataPeriodSelect.value;
        try {
            const historicalData = await api.getHistoricalPerformance(selectedTickers, period);
            const traces = [];
            for (const ticker in historicalData.cumulative_returns) {
                traces.push({
                    x: historicalData.dates,
                    y: historicalData.cumulative_returns[ticker],
                    mode: 'lines',
                    name: ticker
                });
            }
            const layout = { title: 'Cumulative Historical Performance', xaxis: { title: 'Date' }, yaxis: { title: 'Cumulative Return' } };
            Plotly.newPlot(ui.historicalPerformanceGraphDiv, traces, layout);
        } catch (error) {
            ui.historicalPerformanceGraphDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    ui.runMonteCarloBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length === 0) return alert('Please select at least one ETF.');
        const period = ui.dataPeriodSelect.value;
        const numSimulations = parseInt(ui.numSimulationsInput.value);
        const simulationDays = parseInt(ui.simulationDaysInput.value);

        try {
            const results = await api.runMonteCarlo(selectedTickers, period, numSimulations, simulationDays);
            const trace = { x: results.final_returns.map(r => r * 100), type: 'histogram' };
            const layout = { title: 'Monte Carlo: Distribution of Final Returns', xaxis: { title: 'Final Return (%)' } };
            Plotly.newPlot(ui.monteCarloGraphDiv, [trace], layout);
            ui.monteCarloResultsDiv.innerHTML = `<h3>Simulation Results</h3>
                <p><strong>VaR (95%):</strong> ${(results.var_95 * 100).toFixed(2)}%</p>
                <p><strong>CVaR (95%):</strong> ${(results.cvar_95 * 100).toFixed(2)}%</p>`;
        } catch (error) {
            ui.monteCarloResultsDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    ui.analyzeCsvBtn.addEventListener('click', () => {
        const file = ui.csvFileInput.files[0];
        if (!file) return alert('Please select a CSV file.');
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const etfData = await api.analyzeCsv(e.target.result);
                let resultsHtml = '<h3>CSV Analysis</h3><table><thead><tr><th>Ticker</th><th>Return</th><th>Risk</th></tr></thead><tbody>';
                etfData.forEach(item => {
                    resultsHtml += `<tr><td>${item.Ticker}</td><td>${(item.Return * 100).toFixed(2)}%</td><td>${(item.Risk * 100).toFixed(2)}%</td></tr>`;
                });
                resultsHtml += '</tbody></table>';
                ui.csvAnalysisResultsDiv.innerHTML = resultsHtml;
                ui.addTrace({ x: etfData.map(item => item.Risk), y: etfData.map(item => item.Return), mode: 'markers+text', type: 'scatter', name: 'ETFs from CSV', text: etfData.map(item => item.Ticker) });
            } catch (error) {
                ui.csvAnalysisResultsDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
            }
        };
        reader.readAsText(file);
    });

    ui.runDcaSimulationBtn.addEventListener('click', async () => {
        // This button now runs the FUTURE simulation
        const investmentAmount = parseFloat(ui.dcaAmountInput.value);
        if (isNaN(investmentAmount) || investmentAmount <= 0) return alert('Please enter a valid investment amount.');

        const years = parseInt(ui.dcaYearsInput.value);
        if (isNaN(years) || years <= 0) return alert('Please enter a valid number of years.');

        const frequency = ui.dcaFrequencySelect.value;

        // Get the current portfolio's risk and return from the last custom calculation
        const riskText = ui.customPortfolioResultDiv.querySelector('p:nth-of-type(1)')?.textContent || '';
        const returnText = ui.customPortfolioResultDiv.querySelector('p:nth-of-type(2)')?.textContent || '';
        
        const portfolioRiskMatch = riskText.match(/([\d\.]+)/);
        const portfolioReturnMatch = returnText.match(/([\d\.]+)/);

        if (!portfolioRiskMatch || !portfolioReturnMatch) {
            return alert('Please calculate a custom portfolio first to establish its risk/return profile.');
        }

        const portfolioRisk = parseFloat(portfolioRiskMatch[1]) / 100;
        const portfolioReturn = parseFloat(portfolioReturnMatch[1]) / 100;

        try {
            ui.dcaSimulationResultsDiv.innerHTML = '<p>Running future simulation...</p>';
            const results = await api.runFutureDcaSimulation(portfolioReturn, portfolioRisk, investmentAmount, frequency, years);

            if (results.error) throw new Error(results.error);

            const traces = [
                {
                    x: results.time_labels,
                    y: results.upper_scenario,
                    mode: 'lines',
                    name: 'Upper 5% Scenario',
                    line: { color: 'lightgreen', width: 0 }
                },
                {
                    x: results.time_labels,
                    y: results.lower_scenario,
                    mode: 'lines',
                    name: 'Lower 5% Scenario',
                    fill: 'tonexty', // Fill area between upper and lower
                    fillcolor: 'rgba(0,176,246,0.2)',
                    line: { color: 'lightgreen', width: 0 }
                },
                {
                    x: results.time_labels,
                    y: results.mean_scenario,
                    mode: 'lines',
                    name: 'Mean Scenario',
                    line: { color: '#007bff', width: 3 }
                },
                {
                    x: results.time_labels,
                    y: results.total_invested,
                    mode: 'lines',
                    name: 'Total Invested',
                    line: { color: '#6c757d', width: 2, dash: 'dash' }
                }
            ];

            const layout = { 
                title: 'Future DCA Simulation',
                xaxis: { title: 'Years' }, 
                yaxis: { title: 'Portfolio Value' }
            };
            Plotly.newPlot(ui.dcaSimulationGraphDiv, traces, layout);

            ui.dcaSimulationResultsDiv.innerHTML = `<h3>Future Projection Results</h3>
                <p><strong>Total Amount Invested:</strong> ${results.total_invested.slice(-1)[0].toLocaleString(undefined, {style: 'currency', currency: 'USD'})}</p>
                <p><strong>Projected Mean Value:</strong> ${results.final_mean_value.toLocaleString(undefined, {style: 'currency', currency: 'USD'})}</p>`;

        } catch (error) {
            ui.dcaSimulationResultsDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    // --- Initial Page Load ---
    async function initializeApp() {
        try {
            etfDefinitions = await api.getEtfList();
            filterAndDisplayEtfs(); // Initial display based on default filters
            generateMap(); // Initial map generation
        } catch (error) {
            console.error('Initialization failed:', error);
            alert('Could not initialize the application. Please check the console for errors.');
        }
    }

    initializeApp();
});