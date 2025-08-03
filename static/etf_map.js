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

        fetch(`/data?${queryParams.toString()}`)
            .then(response => response.json())
            .then(data => {
                const xData = data.map(item => item.Risk);
                const yData = data.map(item => item.Return);
                const textData = data.map(item => item.Ticker);

                const trace = {
                    x: xData,
                    y: yData,
                    mode: 'markers+text',
                    type: 'scatter',
                    text: textData,
                    textposition: 'top center',
                    marker: { size: 12 }
                };

                const layout = {
                    title: 'ETF Risk-Return Map (Annualized)',
                    xaxis: { title: 'Risk (Annualized Volatility)' },
                    yaxis: { title: 'Expected Return (Annualized)' }
                };

                Plotly.newPlot('graph', [trace], layout);
            })
            .catch(error => console.error('Error fetching ETF data:', error));
    }
});