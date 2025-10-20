import * as api from './api.js';
import * as ui from './ui.js';
import { initAuth } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {

    let currentWeights = {};

    let etfDefinitions = {}; // To store ETF metadata
    let masterCheckedState = new Set(); // Persistent state for all checkboxes

    // Initialize authentication
    initAuth();

    const etfSearchInput = document.getElementById('etf-search-input');

    // --- Event Listeners ---
    ui.assetClassFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.regionFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.styleFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.sizeFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.sectorFilter.addEventListener('change', () => filterAndDisplayEtfs());
    ui.themeFilter.addEventListener('change', () => filterAndDisplayEtfs());
    etfSearchInput.addEventListener('input', () => filterAndDisplayEtfs());

    ui.selectAllBtn.addEventListener('click', () => {
        const visibleTickers = getCurrentlyFilteredTickers();
        visibleTickers.forEach(ticker => masterCheckedState.add(ticker));
        filterAndDisplayEtfs();
    });

    ui.deselectAllBtn.addEventListener('click', () => {
        const visibleTickers = getCurrentlyFilteredTickers();
        visibleTickers.forEach(ticker => masterCheckedState.delete(ticker));
        filterAndDisplayEtfs();
    });

    // Listen for changes on the checkbox container
    ui.etfCheckboxesDiv.addEventListener('change', (event) => {
        if (event.target.type === 'checkbox') {
            const ticker = event.target.value;
            if (event.target.checked) {
                masterCheckedState.add(ticker);
            } else {
                masterCheckedState.delete(ticker);
            }
        }
    });

    // --- Popover Logic ---
    const etfDetailCache = {};
    const sidebar = document.getElementById('sidebar');

    sidebar.addEventListener('show.bs.popover', async (event) => {
        const triggerElement = event.target;
        const ticker = triggerElement.dataset.ticker;
        const popover = bootstrap.Popover.getInstance(triggerElement);

        if (!ticker) return;

        if (etfDetailCache[ticker]) {
            popover.setContent({ '.popover-body': etfDetailCache[ticker] });
            return;
        }

        try {
            const data = await api.getEtfDetails(ticker);

            // --- Build Key Metrics Table ---
            let metricsHtml = '<table class="table table-sm table-borderless mb-2">';
            for (const [key, value] of Object.entries(data.keyMetrics)) {
                metricsHtml += `<tr><td class="fw-bold">${key}</td><td class="text-end">${value}</td></tr>`;
            }
            metricsHtml += '</table>';

            // --- Build Top Holdings Table ---
            let holdingsHtml = '<h6>Top 10 Holdings</h6>';
            if (data.topHoldings && data.topHoldings.length > 0) {
                holdingsHtml += '<table class="table table-sm table-striped table-hover">';
                data.topHoldings.forEach(h => {
                    holdingsHtml += `<tr><td>${h.name}</td><td class="text-end">${h.weight}</td></tr>`;
                });
                holdingsHtml += '</table>';
            } else {
                holdingsHtml += '<p class="text-muted small">No holdings data available.</p>';
            }

            // --- Build Sector Weights Table ---
            let sectorsHtml = '<h6>Sector Weights</h6>';
            if (data.sectorWeights && data.sectorWeights.length > 0) {
                sectorsHtml += '<table class="table table-sm table-striped table-hover">';
                data.sectorWeights.forEach(s => {
                    sectorsHtml += `<tr><td>${s.sector}</td><td class="text-end">${s.weight}</td></tr>`;
                });
                sectorsHtml += '</table>';
            } else {
                sectorsHtml += '<p class="text-muted small">No sector data available.</p>';
            }

            const fullHtml = `
                <div class="etf-popover-content" style="min-width: 320px;">
                    <p class="mb-1"><strong>${data.basicInfo.longName}</strong></p>
                    <p class="text-muted small fst-italic mt-0 mb-2">${data.basicInfo.generatedSummary || ''}</p>
                    <hr class="my-2">
                    ${metricsHtml}
                    <hr class="my-2">
                    ${holdingsHtml}
                    <hr class="my-2">
                    ${sectorsHtml}
                </div>
            `;

            etfDetailCache[ticker] = fullHtml;
            const popoverInstance = bootstrap.Popover.getInstance(triggerElement);
            if (popoverInstance) {
                popoverInstance.setContent({ '.popover-body': fullHtml });
            }

        } catch (error) {
            const errorHtml = `<p class="text-danger">Could not load details. The data may not be available for this ticker.</p>`;
            etfDetailCache[ticker] = errorHtml;
            const popoverInstance = bootstrap.Popover.getInstance(triggerElement);
            if (popoverInstance) {
                popoverInstance.setContent({ '.popover-body': errorHtml });
            }
        }
    });


    // Helper function to get the currently visible tickers based on filters
    function getCurrentlyFilteredTickers() {
        const assetClass = ui.assetClassFilter.value;
        const region = ui.regionFilter.value;
        const style = ui.styleFilter.value;
        const size = ui.sizeFilter.value;
        const sector = ui.sectorFilter.value;
        const theme = ui.themeFilter.value;
        const searchTerm = etfSearchInput.value.normalize('NFKC').toLowerCase();

        return Object.keys(etfDefinitions).filter(ticker => {
            const etf = etfDefinitions[ticker];
            if (!etf) return false;

            // A match is true if the filter is 'all' OR the ETF's property is empty/whitespace OR it matches the filter value.
            const assetMatch = assetClass === 'all' || !etf.asset_class?.trim() || etf.asset_class === assetClass;
            const regionMatch = region === 'all' || !etf.region?.trim() || etf.region === region;
            const styleMatch = style === 'all' || !etf.style?.trim() || etf.style === style;
            const sizeMatch = size === 'all' || !etf.size?.trim() || etf.size === size;
            const sectorMatch = sector === 'all' || !etf.sector?.trim() || etf.sector === sector;
            const themeMatch = theme === 'all' || !etf.theme?.trim() || etf.theme === theme;
            
            const searchMatch = searchTerm === '' || ticker.toLowerCase().includes(searchTerm) || etf.name.toLowerCase().includes(searchTerm);

            return assetMatch && regionMatch && styleMatch && sizeMatch && sectorMatch && themeMatch && searchMatch;
        });
    }

    // Main function to update the checkbox UI
    function filterAndDisplayEtfs() {
        const filteredEtfs = getCurrentlyFilteredTickers();
        ui.createEtfCheckboxes(filteredEtfs, etfDefinitions, ui.etfCheckboxesDiv, masterCheckedState);

        // Initialize popovers after they are created
        const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
        [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
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

    ui.showCorrelationMatrixBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(ui.etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
        if (selectedTickers.length < 2) return alert('Please select at least two ETFs to calculate correlation.');
        const period = ui.dataPeriodSelect.value;
        try {
            const correlationData = await api.getCorrelationMatrix(selectedTickers, period);
            if (correlationData.error) throw new Error(correlationData.error);
            ui.drawCorrelationHeatmap(correlationData, ui.correlationMatrixGraphDiv);
        } catch (error) {
            ui.correlationMatrixGraphDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        }
    });

    // --- Initial Page Load ---
    async function initializeApp() {
        try {
            etfDefinitions = await api.getEtfList();
            masterCheckedState = new Set(Object.keys(etfDefinitions));

            // --- Populate Filters ---
            const getUniqueValues = (prop) => {
                const allValues = Object.values(etfDefinitions).map(etf => etf[prop]).filter(val => val && val.trim() !== '');
                return [...new Set(allValues)].sort();
            };

            ui.populateFilterOptions(ui.styleFilter, getUniqueValues('style'));
            ui.populateFilterOptions(ui.sizeFilter, getUniqueValues('size'));
            ui.populateFilterOptions(ui.sectorFilter, getUniqueValues('sector'));
            ui.populateFilterOptions(ui.themeFilter, getUniqueValues('theme'));
            // Also repopulate existing filters to be fully dynamic
            ui.populateFilterOptions(ui.assetClassFilter, getUniqueValues('asset_class'));
            ui.populateFilterOptions(ui.regionFilter, getUniqueValues('region'));

            filterAndDisplayEtfs(); // Initial display
        } catch (error) {
            console.error('Initialization failed:', error);
            alert('Could not initialize the application. Please check the console for errors.');
        }
    }

    initializeApp();
});