
document.addEventListener('DOMContentLoaded', function() {
    fetch('/data')
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
});
