// static/admin-dashboard.js

// =================================================================================
// デバッグ設定とグローバル変数
// =================================================================================

/**
 * デバッグモードを有効にするフラグ。
 * trueに設定すると、コンソールに詳細なログが出力されます。
 */
const DEBUG = true;

/**
 * Chart.jsのインスタンスを保持するためのグローバル変数。
 * これにより、再描画時に既存のチャートを破棄できます。
 */
let clicksChart, brokerChart, placementChart;


// =================================================================================
// ログおよびユーティリティ関数
// =================================================================================

/**
 * デバッグログを出力します。
 * DEBUGフラグがtrueの場合のみ動作します。
 * @param {...any} args - コンソールに出力する内容。
 */
function log(...args) {
    if (DEBUG) {
        console.log('[Dashboard]', ...args);
    }
}

/**
 * エラーログを常に出力します。
 * @param {...any} args - コンソールに出力するエラー内容。
 */
function logError(...args) {
    console.error('[Dashboard Error]', ...args);
}

/**
 * 指定されたIDのDOM要素のテキスト内容を安全に更新します。
 * 要素が存在しない場合はエラーログを出力します。
 * @param {string} id - 更新する要素のID。
 * @param {string} value - 設定するテキスト内容。
 */
function safeUpdateElement(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    } else {
        logError(`Element #${id} not found`);
    }
}

/**
 * 指定された期間に基づいて開始日と終了日を計算します。
 * @param {string} period - '7d', '30d', '90d'などの期間文字列。
 * @returns {{startDate: string, endDate: string}} YYYY-MM-DD形式の日付オブジェクト。
 */
function calculateDateRange(period) {
    const endDate = new Date();
    let startDate = new Date();

    switch (period) {
        case '7d':
            startDate.setDate(endDate.getDate() - 7);
            break;
        case '30d':
            startDate.setDate(endDate.getDate() - 30);
            break;
        case '90d':
            startDate.setDate(endDate.getDate() - 90);
            break;
        default:
            // デフォルトは30日
            startDate.setDate(endDate.getDate() - 30);
    }

    return {
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
    };
}

/**
 * ローディングインジケーターを表示します。
 * ダッシュボードコンテンツを半透明にし、操作を無効にします。
 */
function showLoading() {
    const container = document.getElementById('dashboard-content');
    if (container) {
        container.style.opacity = '0.5';
        container.style.pointerEvents = 'none';
    }
    log('Loading indicator shown');
}

/**
 * ローディングインジケーターを非表示にします。
 */
function hideLoading() {
    const container = document.getElementById('dashboard-content');
    if (container) {
        container.style.opacity = '1';
        container.style.pointerEvents = 'auto';
    }
    log('Loading indicator hidden');
}

/**
 * エラーメッセージを画面に表示します。
 * 5秒後に自動的に非表示になります。
 * @param {string} message - 表示するエラーメッセージ。
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = `エラー: ${message}`;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        // フォールバックとしてアラートを表示
        alert(`エラーが発生しました: ${message}`);
    }
    logError('Error displayed to user:', message);
}


// =================================================================================
// UI更新関数
// =================================================================================

/**
 * サマリーカード（総クリック数、総CV数など）の表示を更新します。
 * @param {object} stats - APIから取得した統計データ。
 */
function updateSummaryCards(stats) {
    log('Updating summary cards with:', stats);

    try {
        // 総クリック数
        const totalClicks = parseInt(stats.total_clicks) || 0;
        safeUpdateElement('total-clicks', totalClicks.toLocaleString());
        log('Updated total clicks:', totalClicks);

        // 総コンバージョン数
        const totalConversions = parseInt(stats.total_conversions) || 0;
        safeUpdateElement('total-conversions', totalConversions.toLocaleString());
        log('Updated total conversions:', totalConversions);

        // 転換率 (CVR)
        const conversionRate = parseFloat(stats.conversion_rate) || 0;
        safeUpdateElement('conversion-rate', conversionRate.toFixed(2) + '%');
        log('Updated conversion rate:', conversionRate);

        // 推定収益
        const estimatedRevenue = parseFloat(stats.estimated_revenue) || 0;
        const formattedRevenue = '$' + estimatedRevenue.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        safeUpdateElement('estimated-revenue', formattedRevenue);
        log('Updated estimated revenue:', estimatedRevenue);

        log('Summary cards updated successfully');

    } catch (error) {
        logError('Error updating summary cards:', error);
        // エラー発生時、各カードをデフォルト値にリセット
        safeUpdateElement('total-clicks', '0');
        safeUpdateElement('total-conversions', '0');
        safeUpdateElement('conversion-rate', '0.00%');
        safeUpdateElement('estimated-revenue', '$0.00');
    }
}

/**
 * 証券会社ごとのパフォーマンスデータをテーブルに描画します。
 * @param {Array<object>} byBroker - 証券会社ごとの統計データ配列。
 */
function populateDataTable(byBroker) {
    log('Populating data table with:', byBroker);
    const tableBody = document.querySelector('#broker-table tbody');

    if (!tableBody) {
        logError('Element #broker-table tbody not found');
        return;
    }

    // テーブル内容をクリア
    tableBody.innerHTML = '';

    if (!byBroker || byBroker.length === 0) {
        const row = tableBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 5;
        cell.textContent = '表示するデータがありません。';
        cell.style.textAlign = 'center';
        log('No broker data to display');
        return;
    }
    
    // データ行を生成
    byBroker.forEach(item => {
        const row = tableBody.insertRow();
        row.insertCell().textContent = item.broker_name || 'N/A';
        row.insertCell().textContent = (item.clicks || 0).toLocaleString();
        row.insertCell().textContent = (item.conversions || 0).toLocaleString();
        row.insertCell().textContent = (item.conversion_rate || 0).toFixed(2) + '%';
        row.insertCell().textContent = '$' + (item.revenue || 0).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    });

    log('Data table populated successfully');
}


// =================================================================================
// Chart.js 関連の関数
// =================================================================================

/**
 * すべてのチャートを描画するメイン関数。
 * @param {object} stats - APIから取得した統計データ。
 */
function renderCharts(stats) {
    log('Rendering all charts...');
    try {
        renderClicksChart(stats.daily_performance); // 日次パフォーマンスデータを渡す
        renderBrokerPerformanceChart(stats.by_broker);
        renderPlacementChart(stats.by_placement);
        log('All charts rendered successfully');
    } catch (error) {
        logError('Failed to render charts:', error);
    }
}

/**
 * クリック数とコンバージョン数の時系列推移を示す折れ線グラフを描画します。
 * @param {Array<object>} dailyPerformance - 日ごとのパフォーマンスデータ配列。
 */
function renderClicksChart(dailyPerformance = []) {
    const ctx = document.getElementById('clicksChart');
    if (!ctx) {
        logError('Canvas #clicksChart not found');
        return;
    }

    // 既存のチャートがあれば破棄
    if (clicksChart) {
        clicksChart.destroy();
    }
    
    // データが空の場合のデフォルト表示
    const labels = dailyPerformance.length > 0 ? dailyPerformance.map(d => d.date) : ['データなし'];
    const clicksData = dailyPerformance.length > 0 ? dailyPerformance.map(d => d.clicks) : [0];
    const conversionsData = dailyPerformance.length > 0 ? dailyPerformance.map(d => d.conversions) : [0];

    clicksChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'クリック数',
                data: clicksData,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1,
                yAxisID: 'y'
            }, {
                label: 'コンバージョン数',
                data: conversionsData,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'クリック数'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'コンバージョン数'
                    },
                    grid: {
                        drawOnChartArea: false // y1軸のグリッドは非表示
                    }
                }
            }
        }
    });
    log('Clicks chart rendered');
}

/**
 * 証券会社ごとのクリック数を示す棒グラフを描画します。
 * @param {Array<object>} byBroker - 証券会社ごとの統計データ配列。
 */
function renderBrokerPerformanceChart(byBroker = []) {
    const ctx = document.getElementById('brokerPerformanceChart');
    if (!ctx) {
        logError('Canvas #brokerPerformanceChart not found');
        return;
    }

    if (brokerChart) {
        brokerChart.destroy();
    }
    
    // クリック数の多い順にソート
    byBroker.sort((a, b) => (b.clicks || 0) - (a.clicks || 0));

    const labels = byBroker.length > 0 ? byBroker.map(b => b.broker_name) : ['データなし'];
    const clicksData = byBroker.length > 0 ? byBroker.map(b => b.clicks || 0) : [0];

    brokerChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'クリック数',
                data: clicksData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                title: { display: true, text: '証券会社別クリック数' }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        // 整数のみ表示するように調整
                        callback: function(value) {
                            if (Number.isInteger(value)) {
                                return value.toLocaleString();
                            }
                        }
                    }
                }
            }
        }
    });
    log('Broker performance chart rendered');
}

/**
 * 掲載元ごとのクリック数を示す円グラフを描画します。
 * @param {Array<object>} byPlacement - 掲載元ごとの統計データ配列。
 */
function renderPlacementChart(byPlacement = []) {
    const ctx = document.getElementById('placementChart');
    if (!ctx) {
        logError('Canvas #placementChart not found');
        return;
    }

    if (placementChart) {
        placementChart.destroy();
    }
    
    const labels = byPlacement.length > 0 ? byPlacement.map(p => p.placement_id) : ['データなし'];
    const clicksData = byPlacement.length > 0 ? byPlacement.map(p => p.clicks || 0) : [0];
    
    placementChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: 'クリック数',
                data: clicksData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: '掲載元別クリック数' }
            }
        }
    });
    log('Placement chart rendered');
}


// =================================================================================
// データ取得とメインロジック
// =================================================================================

/**
 * サーバーからダッシュボードのデータを非同期で読み込み、UIを更新します。
 * @param {string|null} startDate - 取得期間の開始日 (YYYY-MM-DD)。
 * @param {string|null} endDate - 取得期間の終了日 (YYYY-MM-DD)。
 */
async function loadDashboardData(startDate = null, endDate = null) {
    log('Loading dashboard data...', { startDate, endDate });

    try {
        showLoading();

        // 日付が指定されていない場合は、デフォルトで過去30日の範囲を使用
        if (!startDate || !endDate) {
            const range = calculateDateRange('30d');
            startDate = range.startDate;
            endDate = range.endDate;
        }

        const url = `/api/admin/affiliate/stats?start_date=${startDate}&end_date=${endDate}`;
        log('Fetching from:', url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        log('Received data:', data);

        // APIレスポンスが `data.data` の階層を持つ場合と持たない場合の両方に対応
        const stats = data.data || data;
        log('Processed stats:', stats);

        // Nullish coalescing operator (??) を使用して、各プロパティのnull/undefinedを安全に処理
        const safeStats = {
            total_clicks: stats.total_clicks ?? 0,
            total_conversions: stats.total_conversions ?? 0,
            conversion_rate: stats.conversion_rate ?? 0,
            estimated_revenue: stats.estimated_revenue ?? 0,
            daily_performance: Array.isArray(stats.daily_performance) ? stats.daily_performance : [],
            by_broker: Array.isArray(stats.by_broker) ? stats.by_broker : [],
            by_placement: Array.isArray(stats.by_placement) ? stats.by_placement : [],
            period: stats.period || { start: startDate, end: endDate }
        };

        log('Safe stats:', safeStats);

        // 各UIコンポーネントを更新
        updateSummaryCards(safeStats);
        renderCharts(safeStats);
        populateDataTable(safeStats.by_broker);

        hideLoading();
        log('Dashboard loaded successfully');

    } catch (error) {
        logError('Failed to load dashboard:', error);
        showError(error.message); // ユーザーにエラーを通知
        hideLoading();
    }
}


// =================================================================================
// イベントリスナー
// =================================================================================

/**
 * 期間選択プルダウンが変更されたときに発火するハンドラ。
 * @param {Event} event - changeイベントオブジェクト。
 */
function handlePeriodChange(event) {
    const period = event.target.value;
    log(`Period changed to: ${period}`);
    const { startDate, endDate } = calculateDateRange(period);
    loadDashboardData(startDate, endDate);
}

/**
 * DOMの読み込みが完了した時点で初期化処理を実行します。
 */
document.addEventListener('DOMContentLoaded', () => {
    log('Dashboard initializing...');

    const periodSelect = document.getElementById('period-select');
    if (periodSelect) {
        periodSelect.addEventListener('change', handlePeriodChange);
        log('Period selector event listener attached');
    } else {
        logError('Period selector #period-select not found');
    }

    // 初期データを読み込む
    loadDashboardData();
});