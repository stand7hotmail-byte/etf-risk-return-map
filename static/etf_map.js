document.addEventListener('DOMContentLoaded', function() {
    const etfCheckboxesDiv = document.getElementById('etf-checkboxes');
    const generateMapBtn = document.getElementById('generate-map-btn');

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

    function generateMap() {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF.');
            Plotly.purge('graph'); // グラフをクリア
            return;
        }

        const queryParams = new URLSearchParams();
        selectedTickers.forEach(ticker => queryParams.append('tickers', ticker));

        // ETFデータ、効率的フロンティアデータ、リスクフリーレートを並行してフェッチ
        Promise.all([
            fetch(`/data?${queryParams.toString()}`).then(response => response.json()),
            fetch(`/efficient_frontier?${queryParams.toString()}`).then(response => response.json()),
            fetch('/risk_free_rate').then(response => response.json())
        ])
        .then(([etfData, frontierData, riskFreeRateData]) => {
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
                marker: { size: 12 }
            });

            // 効率的フロンティアのトレース
            traces.push({
                x: frontierData.map(item => item.Risk),
                y: frontierData.map(item => item.Return),
                mode: 'lines',
                type: 'scatter',
                name: 'Efficient Frontier',
                line: { color: 'blue', width: 2 }
            });

            // リスクフリーレートのトレース
            const riskFreeRate = riskFreeRateData.risk_free_rate;
            traces.push({
                x: [0], // リスクは0
                y: [riskFreeRate], // リスクフリーレートのリターン
                mode: 'markers',
                type: 'scatter',
                name: 'Risk-Free Rate',
                marker: { size: 20, color: 'green', symbol: 'star' } // サイズを大きくする
            });

            const layout = {
                title: 'ETF Risk-Return Map (Annualized)',
                xaxis: { title: 'Risk (Annualized Volatility)' },
                yaxis: { title: 'Expected Return (Annualized)' }
            };

            Plotly.newPlot('graph', traces, layout);
        })
        .catch(error => console.error('Error fetching data:', error));
    }
});