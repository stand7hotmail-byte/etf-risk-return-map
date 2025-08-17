document.addEventListener('DOMContentLoaded', function() {
    const etfCheckboxesDiv = document.getElementById('etf-checkboxes');
    const generateMapBtn = document.getElementById('generate-map-btn');
    const dataPeriodSelect = document.getElementById('data-period-select');
    const compositionDetailsDiv = document.getElementById('composition-details');
    const portfolioSlidersDiv = document.getElementById('portfolio-sliders');
    const calculateCustomPortfolioBtn = document.getElementById('calculate-custom-portfolio-btn');
    const customPortfolioResultDiv = document.getElementById('custom-portfolio-result');
    const targetReturnInput = document.getElementById('target-return-input');
    const optimizeByReturnBtn = document.getElementById('optimize-by-return-btn');
    const targetRiskInput = document.getElementById('target-risk-input');
    const optimizeByRiskBtn = document.getElementById('optimize-by-risk-btn');
    const targetOptimizationResultDiv = document.getElementById('target-optimization-result');

    let currentWeights = {}; // グローバル変数として定義

    // ETFリストを取得してチェックボックスを生成
    fetch('/etf_list')
        .then(response => response.json())
        .then(etfList => {
            etfList.forEach(ticker => {
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = ticker;
                checkbox.checked = true; // デフォルトで全て選択
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(ticker));
                etfCheckboxesDiv.appendChild(label);
            });
            generateMap(); // 初期表示
        })
        .catch(error => console.error('Error fetching ETF list:', error));

    // マップ生成ボタンのイベントリスナー
    generateMapBtn.addEventListener('click', generateMap);

    // カスタムポートフォリオ計算ボタンのイベントリスナー
    calculateCustomPortfolioBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF to create a custom portfolio.');
            customPortfolioResultDiv.innerHTML = '';
            return;
        }

        // 現在のスライダーの値を収集し、正規化
        let totalWeight = 0;
        const rawWeights = {};
        selectedTickers.forEach(ticker => {
            const slider = portfolioSlidersDiv.querySelector(`input[data-ticker="${ticker}"]`);
            if (slider) {
                rawWeights[ticker] = parseFloat(slider.value);
                totalWeight += rawWeights[ticker];
            } else {
                // スライダーがない場合は、初期値（均等）を使用
                rawWeights[ticker] = 100 / selectedTickers.length;
                totalWeight += rawWeights[ticker];
            }
        });

        if (totalWeight === 0) {
            alert('Please set non-zero weights for your custom portfolio.');
            return;
        }

        const normalizedWeights = {};
        selectedTickers.forEach(ticker => {
            normalizedWeights[ticker] = rawWeights[ticker] / totalWeight;
        });

        const period = dataPeriodSelect.value;

        // バックエンドにカスタムポートフォリオデータをリクエスト
        try {
            const response = await fetch('/custom_portfolio_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    weights: normalizedWeights,
                    period: period
                })
            });
            const customPortfolioData = await response.json();

            if (customPortfolioData.error) {
                customPortfolioResultDiv.innerHTML = `<p style="color: red;">Error: ${customPortfolioData.error}</p>`;
                return;
            }

            // 結果を表示
            customPortfolioResultDiv.innerHTML = `
                <h3>Your Custom Portfolio</h3>
                <p><strong>Risk:</strong> ${(customPortfolioData.Risk * 100).toFixed(2)}%</p>
                <p><strong>Return:</strong> ${(customPortfolioData.Return * 100).toFixed(2)}%</p>
            `;

            // グラフにカスタムポートフォリオの点を追加
            const graphDiv = document.getElementById('graph');
            const currentData = graphDiv.data || [];

            // 既存のカスタムポートフォリオの点を削除（もしあれば）
            const updatedData = currentData.filter(trace => trace.name !== 'Your Custom Portfolio');

            updatedData.push({
                x: [customPortfolioData.Risk],
                y: [customPortfolioData.Return],
                mode: 'markers',
                type: 'scatter',
                name: 'Your Custom Portfolio',
                marker: { size: 15, color: 'purple', symbol: 'star' },
                hovertemplate:
                    '<b>Your Custom Portfolio</b><br>' +
                    '<b>Risk:</b> %{x:.2%}<br>' +
                    '<b>Return:</b> %{y:.2%}'
            });

            Plotly.react('graph', updatedData, graphDiv.layout);

        } catch (error) {
            console.error('Error calculating custom portfolio:', error);
            customPortfolioResultDiv.innerHTML = '<p style="color: red;">An error occurred while calculating your custom portfolio.</p>';
        }
    });

    // Optimize by Returnボタンのイベントリスナー
    optimizeByReturnBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF to optimize.');
            targetOptimizationResultDiv.innerHTML = '';
            return;
        }

        const targetReturn = parseFloat(targetReturnInput.value) / 100; // パーセンテージを小数に変換
        if (isNaN(targetReturn) || targetReturn <= 0) {
            alert('Please enter a valid positive target return.');
            return;
        }

        const period = dataPeriodSelect.value;

        try {
            const response = await fetch('/optimize_by_return', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    target_value: targetReturn,
                    period: period
                })
            });
            const result = await response.json();

            if (result.error) {
                targetOptimizationResultDiv.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                return;
            }

            targetOptimizationResultDiv.innerHTML = `
                <h3>Optimized Portfolio (Target Return)</h3>
                <p><strong>Target Return:</strong> ${(targetReturn * 100).toFixed(2)}%</p>
                <p><strong>Achieved Return:</strong> ${(result.Return * 100).toFixed(2)}%</p>
                <p><strong>Risk:</strong> ${(result.Risk * 100).toFixed(2)}%</p>
                <h4>Composition:</h4>
                <table>
                    <thead><tr><th>ETF</th><th>Weight</th></tr></thead>
                    <tbody>
                        ${Object.entries(result.weights).map(([ticker, weight]) => `<tr><td>${ticker}</td><td>${(weight * 100).toFixed(2)}%</td></tr>`).join('')}
                    </tbody>
                </table>
            `;

            // グラフに最適化されたポートフォリオの点を追加
            const graphDiv = document.getElementById('graph');
            const currentData = graphDiv.data || [];
            const updatedData = currentData.filter(trace => trace.name !== 'Optimized by Return');

            updatedData.push({
                x: [result.Risk],
                y: [result.Return],
                mode: 'markers',
                type: 'scatter',
                name: 'Optimized by Return',
                marker: { size: 15, color: 'blue', symbol: 'circle' },
                hovertemplate:
                    '<b>Optimized by Return</b><br>' +
                    '<b>Risk:</b> %{x:.2%}<br>' +
                    '<b>Return:</b> %{y:.2%}'
            });

            Plotly.react('graph', updatedData, graphDiv.layout);

        } catch (error) {
            console.error('Error optimizing by return:', error);
            targetOptimizationResultDiv.innerHTML = '<p style="color: red;">An error occurred while optimizing by return.</p>';
        }
    });

    // Optimize by Riskボタンのイベントリスナー
    optimizeByRiskBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF to optimize.');
            targetOptimizationResultDiv.innerHTML = '';
            return;
        }

        const targetRisk = parseFloat(targetRiskInput.value) / 100; // パーセンテージを小数に変換
        if (isNaN(targetRisk) || targetRisk <= 0) {
            alert('Please enter a valid positive target risk.');
            return;
        }

        const period = dataPeriodSelect.value;

        try {
            const response = await fetch('/optimize_by_risk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    target_value: targetRisk,
                    period: period
                })
            });
            const result = await response.json();

            if (result.error) {
                targetOptimizationResultDiv.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                return;
            }

            targetOptimizationResultDiv.innerHTML = `
                <h3>Optimized Portfolio (Target Risk)</h3>
                <p><strong>Target Risk:</strong> ${(targetRisk * 100).toFixed(2)}%</p>
                <p><strong>Achieved Risk:</strong> ${(result.Risk * 100).toFixed(2)}%</p>
                <p><strong>Return:</strong> ${(result.Return * 100).toFixed(2)}%</p>
                <h4>Composition:</h4>
                <table>
                    <thead><tr><th>ETF</th><th>Weight</th></tr></thead>
                    <tbody>
                        ${Object.entries(result.weights).map(([ticker, weight]) => `<tr><td>${ticker}</td><td>${(weight * 100).toFixed(2)}%</td></tr>`).join('')}
                    </tbody>
                </table>
            `;

            // グラフに最適化されたポートフォリオの点を追加
            const graphDiv = document.getElementById('graph');
            const currentData = graphDiv.data || [];
            const updatedData = currentData.filter(trace => trace.name !== 'Optimized by Risk');

            updatedData.push({
                x: [result.Risk],
                y: [result.Return],
                mode: 'markers',
                type: 'scatter',
                name: 'Optimized by Risk',
                marker: { size: 15, color: 'green', symbol: 'square' },
                hovertemplate:
                    '<b>Optimized by Risk</b><br>' +
                    '<b>Risk:</b> %{x:.2%}<br>' +
                    '<b>Return:</b> %{y:.2%}'
            });

            Plotly.react('graph', updatedData, graphDiv.layout);

        } catch (error) {
            console.error('Error optimizing by risk:', error);
            targetOptimizationResultDiv.innerHTML = '<p style="color: red;">An error occurred while optimizing by risk.</p>';
        }
    });

    function generateMap() {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF.');
            Plotly.purge('graph'); // グラフをクリア
            compositionDetailsDiv.innerHTML = 'Select ETFs and click \'Generate Map\' to see composition.';
            portfolioSlidersDiv.innerHTML = ''; // スライダーもクリア
            customPortfolioResultDiv.innerHTML = ''; // 結果もクリア
            return;
        }

        // カスタムポートフォリオのスライダーを生成
        portfolioSlidersDiv.innerHTML = ''; // 既存のスライダーをクリア
        const initialWeight = 100 / selectedTickers.length;
        const currentWeights = {};

        selectedTickers.forEach(ticker => {
            const sliderContainer = document.createElement('div');
            sliderContainer.style.marginBottom = '10px';
            sliderContainer.innerHTML = `
                <label>${ticker}: <span id="${ticker}-weight">${initialWeight.toFixed(2)}%</span></label>
                <input type="range" min="0" max="100" value="${initialWeight}" step="0.01" data-ticker="${ticker}" style="width: 100%;">
            `;
            portfolioSlidersDiv.appendChild(sliderContainer);
            currentWeights[ticker] = initialWeight;
        });

        // スライダーのイベントリスナーを設定
        portfolioSlidersDiv.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.oninput = (event) => {
                const changedTicker = event.target.dataset.ticker;
                const changedValue = parseFloat(event.target.value);
                currentWeights[changedTicker] = changedValue;
                updateSliderPercentages(changedTicker, changedValue);
            };
        });

        function updateSliderPercentages(changedTicker, changedValue) {
            // 個々のスライダーのパーセンテージを更新
            document.getElementById(`${changedTicker}-weight`).textContent = `${changedValue.toFixed(2)}%`;

            // ここで合計が100%になるように他のスライダーを調整するロジックを後で追加
            // 現時点では、個々のスライダーの表示のみを更新
        }

        // 初期表示時にカスタムポートフォリオの結果をクリア
        customPortfolioResultDiv.innerHTML = '';

        const queryParams = new URLSearchParams();
        selectedTickers.forEach(ticker => queryParams.append('tickers', ticker));
        const period = dataPeriodSelect.value;
        queryParams.append('period', period);

        // ETFデータ、効率的フロンティアデータ、リスクフリーレートを並行してフェッチ
        Promise.all([
            fetch(`/data?${queryParams.toString()}`).then(response => response.json()),
            fetch(`/efficient_frontier?${queryParams.toString()}`).then(response => response.json()),
            fetch('/risk_free_rate').then(response => response.json())
        ])
        .then(([etfData, frontierDataResponse, riskFreeRateData]) => {
            console.log("DEBUG: frontierDataResponse:", frontierDataResponse); // 追加
            const traces = [];

            // ETFデータのトレース
            traces.push({
                x: etfData.map(item => item.Risk),
                y: etfData.map(item => item.Return),
                mode: 'markers+text',
                type: 'scatter',
                name: 'ETFs',
                text: etfData.map(item => item.Ticker),
                textposition: 'top center',
                marker: { size: 12 },
                hovertemplate:
                    '<b>%{text}</b><br>'+'<b>Risk:</b> %{x:.2%}<br>'+'<b>Return:</b> %{y:.2%}'
            });

            // 効率的フロンティアのトレース
            traces.push({
                x: frontierDataResponse.frontier_points.map(item => item.Risk),
                y: frontierDataResponse.frontier_points.map(item => item.Return),
                mode: 'lines',
                type: 'scatter',
                name: 'Efficient Frontier',
                line: { color: 'blue', width: 2 },
                hovertemplate:
                    '<b>Risk:</b> %{x:.2%}<br>'+'<b>Return:</b> %{y:.2%}'
            });

            // リスクフリーレートのトレース
            const riskFreeRate = riskFreeRateData.risk_free_rate;
            traces.push({
                x: [0], // リスクは0
                y: [riskFreeRate], // リスクフリーレートのリターン
                mode: 'markers',
                type: 'scatter',
                name: 'Risk-Free Rate',
                marker: { size: 20, color: 'green', symbol: 'star' },
                hovertemplate:
                    '<b>Risk-Free Rate</b><br>'+'<b>Return:</b> %{y:.2%}'
            });

            // 資本市場線 (CML) のトレース
            const tangencyPortfolio = frontierDataResponse.tangency_portfolio;
            const tangencyPortfolioWeights = frontierDataResponse.tangency_portfolio_weights;

            if (tangencyPortfolio) {
                console.log("DEBUG: Tangency Portfolio (JS):", tangencyPortfolio);

                console.log("DEBUG: Before CML trace push.");
                traces.push({
                    x: [0, tangencyPortfolio.Risk],
                    y: [riskFreeRate, tangencyPortfolio.Return],
                    mode: 'lines',
                    type: 'scatter',
                    name: 'Capital Market Line',
                    line: { color: 'red', width: 2, dash: 'dash' },
                    hovertemplate:
                        '<b>Capital Market Line</b><br>' +
                        '<b>Risk:</b> %{x:.2%}<br>' +
                        '<b>Return:</b> %{y:.2%}'
                });
                console.log("DEBUG: After CML trace push.");

                console.log("DEBUG: Before Max Sharpe Ratio Portfolio trace push.");
                traces.push({
                    x: [tangencyPortfolio.Risk],
                    y: [tangencyPortfolio.Return],
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Max Sharpe Ratio Portfolio',
                    marker: { size: 15, color: 'darkorange', symbol: 'diamond' },
                    customdata: [tangencyPortfolio.SharpeRatio],
                    hovertemplate:
                        '<b>Max Sharpe Ratio Portfolio</b><br>' +
                        '<b>Risk:</b> %{x:.2%}<br>' +
                        '<b>Return:</b> %{y:.2%}<br>' +
                        '<b>Sharpe Ratio:</b> %{customdata:.2f}'
                });
                console.log("DEBUG: After Max Sharpe Ratio Portfolio trace push.");

                // ポートフォリオ構成比率の表示
                if (Object.keys(tangencyPortfolioWeights).length > 0) {
                    let compositionHtml = '<table><thead><tr><th>ETF Ticker</th><th>Weight</th></tr></thead><tbody>';
                    for (const ticker in tangencyPortfolioWeights) {
                        compositionHtml += `<tr><td>${ticker}</td><td>${(tangencyPortfolioWeights[ticker] * 100).toFixed(2)}%</td></tr>`;
                    }
                    compositionHtml += '</tbody></table>';
                    compositionDetailsDiv.innerHTML = compositionHtml;
                } else {
                    compositionDetailsDiv.innerHTML = 'Could not calculate Max Sharpe Ratio Portfolio composition for selected ETFs.';
                }
                console.log("DEBUG: Composition section updated with actual data.");

            } else {
                compositionDetailsDiv.innerHTML = 'Could not calculate Max Sharpe Ratio Portfolio composition.';
            }

            // 全てのリスク値を取得し、最大値を決定
            const allRisks = etfData.map(item => item.Risk)
                                .concat(frontierDataResponse.frontier_points.map(item => item.Risk));
            if (tangencyPortfolio) {
                allRisks.push(tangencyPortfolio.Risk);
            }
            const maxRisk = Math.max(...allRisks);

            // 全てのリターン値を取得し、最大値と最小値を決定
            const allReturns = etfData.map(item => item.Return)
                                  .concat(frontierDataResponse.frontier_points.map(item => item.Return));
            if (tangencyPortfolio) {
                allReturns.push(tangencyPortfolio.Return);
            }
            allReturns.push(riskFreeRate); // リスクフリーレートも考慮
            const minReturn = Math.min(...allReturns);
            const maxReturn = Math.max(...allReturns);

            const layout = {
                title: 'ETF Risk-Return Map (Annualized)',
                xaxis: {
                    title: 'Risk (Annualized Volatility)',
                    range: [0, maxRisk * 1.1] // X軸を0から開始し、最大値はデータの最大値より少し大きく設定
                },
                yaxis: {
                    title: 'Expected Return (Annualized)',
                    range: [minReturn * 0.9, maxReturn * 1.1] // Y軸の範囲も動的に調整
                }
            };

            Plotly.newPlot('graph', traces, layout);
        })
        .catch(error => console.error('Error fetching data:', error));
    }
});