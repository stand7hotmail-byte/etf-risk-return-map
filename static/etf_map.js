document.addEventListener('DOMContentLoaded', function() {

    // --- Firebase Configuration ---
    const firebaseConfig = {
      apiKey: "AIzaSyAwlMjilSEaZlSXnEC4NQgOV_gwYqLQ1co", // ★★★ 後で必ず設定してください ★★★設定済
      authDomain: "etf-webapp.firebaseapp.com",
      projectId: "etf-webapp",
      storageBucket: "etf-webapp.appspot.com",
      messagingSenderId: "761377330809",
      appId: "1:761377330809:web:cd0f5a80a6c105ab2aa6a8"
    };

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();
    // --- End of Firebase Configuration ---

    const etfCheckboxesDiv = document.getElementById('etf-checkboxes');
    const constraintInputsDiv = document.getElementById('constraint-inputs');
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
    const showHistoricalPerformanceBtn = document.getElementById('show-historical-performance-btn');
    const historicalPerformanceGraphDiv = document.getElementById('historical-performance-graph');
    const numSimulationsInput = document.getElementById('num-simulations-input');
    const simulationDaysInput = document.getElementById('simulation-days-input');
    const runMonteCarloBtn = document.getElementById('run-monte-carlo-btn');
    const monteCarloGraphDiv = document.getElementById('monte-carlo-graph');
    const monteCarloResultsDiv = document.getElementById('monte-carlo-results');
    const csvFileInput = document.getElementById('csv-file-input');
    const analyzeCsvBtn = document.getElementById('analyze-csv-btn');
    const csvAnalysisResultsDiv = document.getElementById('csv-analysis-results');
    const csvAnalysisGraphDiv = document.getElementById('csv-analysis-graph');

    // 認証関連の要素
    const authUsernameInput = document.getElementById('auth-username');
    const authPasswordInput = document.getElementById('auth-password');
    const registerBtn = document.getElementById('register-btn');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const googleLoginBtn = document.getElementById('google-login-btn');
    const authMessageDiv = document.getElementById('auth-message');
    const loggedInUserDiv = document.getElementById('logged-in-user');

    // ポートフォリオ管理関連の要素
    const portfolioNameInput = document.getElementById('portfolio-name-input');
    const savePortfolioBtn = document.getElementById('save-portfolio-btn');
    const listPortfoliosBtn = document.getElementById('list-portfolios-btn');
    const savedPortfoliosSelect = document.getElementById('saved-portfolios-select');
    const loadPortfolioBtn = document.getElementById('load-portfolio-btn');
    const deletePortfolioBtn = document.getElementById('delete-portfolio-btn');
    const portfolioMessageDiv = document.getElementById('portfolio-message');

    let accessToken = localStorage.getItem('access_token');

    // 認証ヘッダーを取得するヘルパー関数
    function getAuthHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (accessToken) {
            headers['Authorization'] = `Bearer ${accessToken}`;
        }
        return headers;
    }

    // 認証UIの状態を更新
    function updateAuthUI() {
        console.log("updateAuthUI called.");
        console.log("accessToken:", accessToken);
        if (accessToken) {
            console.log("Attempting to decode token...");
            try {
                const decodedToken = jwt_decode(accessToken);
                console.log("Decoded token:", decodedToken);
                loginBtn.style.display = 'none';
                registerBtn.style.display = 'none';
                logoutBtn.style.display = 'inline-block';
                loggedInUserDiv.style.display = 'block';
                loggedInUserDiv.querySelector('strong').textContent = decodedToken.sub;
            } catch (e) {
                console.error("Error decoding JWT:", e);
                accessToken = null; // 無効なトークンをクリア
                localStorage.removeItem('access_token');
                authMessageDiv.style.color = 'red';
                authMessageDiv.textContent = 'Invalid token. Please log in again.';
                updateAuthUI(); // UIをリセット
            }
        } else {
            console.log("No accessToken.");
            loginBtn.style.display = 'inline-block';
            registerBtn.style.display = 'inline-block';
            logoutBtn.style.display = 'none';
            loggedInUserDiv.style.display = 'none';
            loggedInUserDiv.querySelector('strong').textContent = '';
        }
    }

    // ページロード時にUIを更新
    updateAuthUI();

    // 登録ボタンのイベントリスナー
    registerBtn.addEventListener('click', async () => {
        const username = authUsernameInput.value;
        const password = authPasswordInput.value;
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const result = await response.json();
            if (response.ok) {
                authMessageDiv.style.color = 'green';
                authMessageDiv.textContent = `User ${result.username} registered successfully!`;
            } else {
                authMessageDiv.style.color = 'red';
                authMessageDiv.textContent = result.detail || 'Registration failed.';
            }
        } catch (error) {
            authMessageDiv.style.color = 'red';
            authMessageDiv.textContent = 'An error occurred during registration.';
        }
    });

    // ログインボタンのイベントリスナー
    loginBtn.addEventListener('click', async () => {
        const username = authUsernameInput.value;
        const password = authPasswordInput.value;
        const form_data = new URLSearchParams();
        form_data.append('username', username);
        form_data.append('password', password);

        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: form_data
            });
            const result = await response.json();
            if (response.ok) {
                accessToken = result.access_token;
                localStorage.setItem('access_token', accessToken);
                authMessageDiv.style.color = 'green';
                authMessageDiv.textContent = 'Logged in successfully!';
                updateAuthUI(); // UI update will happen when jwt-decode script loads (handled by script.onload)
            } else {
                authMessageDiv.style.color = 'red';
                authMessageDiv.textContent = result.detail || 'Login failed.';
            }
        } catch (error) {
            authMessageDiv.style.color = 'red';
            authMessageDiv.textContent = 'An error occurred during login.';
        }
    });

    // ログアウトボタンのイベントリスナー
    logoutBtn.addEventListener('click', () => {
        accessToken = null;
        localStorage.removeItem('access_token');
        authMessageDiv.style.color = 'green';
        authMessageDiv.textContent = 'Logged out successfully!';
        updateAuthUI();
    });

    // Googleログインボタンのイベントリスナー
    googleLoginBtn.addEventListener('click', () => {
        const provider = new firebase.auth.GoogleAuthProvider();
        auth.signInWithPopup(provider)
            .then(async (result) => {
                // FirebaseのIDトークンを取得
                const firebaseIdToken = await result.user.getIdToken();

                // バックエンドにIDトークンを送信して、内部トークンを取得
                const response = await fetch('/token/google', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: firebaseIdToken })
                });

                const data = await response.json();
                if (response.ok) {
                    accessToken = data.access_token;
                    localStorage.setItem('access_token', accessToken);
                    authMessageDiv.style.color = 'green';
                    authMessageDiv.textContent = 'Logged in successfully with Google!';
                    updateAuthUI();
                } else {
                    throw new Error(data.detail || 'Google login failed.');
                }
            })
            .catch((error) => {
                console.error('Google Sign-In Error:', error);
                authMessageDiv.style.color = 'red';
                authMessageDiv.textContent = `Google login error: ${error.message}`;
            });
    });

    // ポートフォリオ保存ボタンのイベントリスナー
    savePortfolioBtn.addEventListener('click', async () => {
        if (!accessToken) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please log in to save portfolios.';
            return;
        }
        const portfolioName = portfolioNameInput.value;
        if (!portfolioName) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please enter a portfolio name.';
            return;
        }

        // 現在のUIの状態を収集 (簡略版)
        const portfolioState = {
            selectedTickers: Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value),
            dataPeriod: dataPeriodSelect.value,
            weights: currentWeights // 現在のスライダーの比率を保存
        };

        try {
            const response = await fetch('/save_portfolio', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ name: portfolioName, content: portfolioState })
            });
            const result = await response.json();
            if (response.ok) {
                portfolioMessageDiv.style.color = 'green';
                portfolioMessageDiv.textContent = result.message;
                // 保存後、ポートフォリオリストを更新
                listPortfoliosBtn.click();
            } else {
                portfolioMessageDiv.style.color = 'red';
                portfolioMessageDiv.textContent = result.detail || 'Failed to save portfolio.';
            }
        } catch (error) {
            console.error('Error saving portfolio:', error);
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'An error occurred while saving portfolio.';
        }
    });

    // ポートフォリオリスト取得ボタンのイベントリスナー
    listPortfoliosBtn.addEventListener('click', async () => {
        if (!accessToken) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please log in to list portfolios.';
            return;
        }
        try {
            const response = await fetch('/list_portfolios', {
                method: 'GET',
                headers: getAuthHeaders()
            });
            const portfolios = await response.json();
            if (response.ok) {
                savedPortfoliosSelect.innerHTML = ''; // クリア
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
                portfolioMessageDiv.style.color = 'green';
                portfolioMessageDiv.textContent = 'Portfolios loaded.';
            } else {
                portfolioMessageDiv.style.color = 'red';
                portfolioMessageDiv.textContent = result.detail || 'Failed to list portfolios.';
            }
        } catch (error) {
            console.error('Error listing portfolios:', error);
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'An error occurred while listing portfolios.';
        }
    });

    // Helper function to apply a loaded portfolio state to the UI
    function applyPortfolioState(state) {
        if (!state || !state.selectedTickers) {
            return; // Silently fail if state is invalid
        }

        // 1. Update ETF Checkboxes
        const allCheckboxes = etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]');
        allCheckboxes.forEach(checkbox => {
            checkbox.checked = state.selectedTickers.includes(checkbox.value);
        });

        // 2. Update Data Period
        if (state.dataPeriod) {
            dataPeriodSelect.value = state.dataPeriod;
        }

        // 3. Define the action to take after the main map is generated
        const postGenerationAction = () => {
            if (state.weights) {
                // Restore slider weights
                for (const ticker in state.weights) {
                    const weight = state.weights[ticker];
                    const slider = portfolioSlidersDiv.querySelector(`input[data-ticker="${ticker}"]`);
                    const weightSpan = document.getElementById(`${ticker}-weight`);

                    if (slider && weightSpan) {
                        slider.value = weight;
                        weightSpan.textContent = `${parseFloat(weight).toFixed(2)}%`;
                        currentWeights[ticker] = parseFloat(weight);
                    }
                }
                // After restoring weights, calculate and show the custom portfolio point
                calculateCustomPortfolioBtn.click();
            }
        };

        // 4. Regenerate the map and pass the post-action as a callback
        generateMap(postGenerationAction);
    }

    // ポートフォリオ読み込みボタンのイベントリスナー
    loadPortfolioBtn.addEventListener('click', async () => {
        if (!accessToken) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please log in to load portfolios.';
            return;
        }
        const portfolioId = savedPortfoliosSelect.value;
        if (!portfolioId) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please select a portfolio to load.';
            return;
        }
        try {
            const response = await fetch(`/load_portfolio/${portfolioId}`, {
                method: 'GET',
                headers: getAuthHeaders()
            });
            const loadedData = await response.json();
            if (response.ok) {
                portfolioMessageDiv.style.color = 'green';
                portfolioMessageDiv.textContent = `Portfolio ${portfolioId} loaded. Applying state...`;
                applyPortfolioState(loadedData);
            } else {
                portfolioMessageDiv.style.color = 'red';
                portfolioMessageDiv.textContent = loadedData.detail || 'Failed to load portfolio.';
            }
        } catch (error) {
            console.error('Error loading portfolio:', error);
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'An error occurred while loading portfolio.';
        }
    });

    // ポートフォリオ削除ボタンのイベントリスナー
    deletePortfolioBtn.addEventListener('click', async () => {
        if (!accessToken) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please log in to delete portfolios.';
            return;
        }
        const portfolioId = savedPortfoliosSelect.value;
        if (!portfolioId) {
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'Please select a portfolio to delete.';
            return;
        }
        if (!confirm('Are you sure you want to delete this portfolio?')) {
            return;
        }
        try {
            const response = await fetch(`/delete_portfolio/${portfolioId}`, {
                method: 'DELETE',
                headers: getAuthHeaders()
            });
            const result = await response.json();
            if (response.ok) {
                portfolioMessageDiv.style.color = 'green';
                portfolioMessageDiv.textContent = result.message;
                // 削除後、ポートフォリオリストを更新
                listPortfoliosBtn.click();
            } else {
                portfolioMessageDiv.style.color = 'red';
                portfolioMessageDiv.textContent = result.detail || 'Failed to delete portfolio.';
            }
        } catch (error) {
            console.error('Error deleting portfolio:', error);
            portfolioMessageDiv.style.color = 'red';
            portfolioMessageDiv.textContent = 'An error occurred while deleting portfolio.';
        }
    });

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
                headers: { 'Content-Type': 'application/json' },
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

            // 既存のCSVからのプロットを削除（もしあれば）
            const updatedData = currentData.filter(trace => trace.name !== 'Your Custom Portfolio');

            updatedData.push({
                x: [customPortfolioData.Risk],
                y: [customPortfolioData.Return],
                mode: 'markers',
                type: 'scatter',
                name: 'Your Custom Portfolio',
                marker: { size: 15, color: 'purple', symbol: 'star' },
                hovertemplate:
                    '<b>Your Custom Portfolio</b><br>'
                    +'<b>Risk:</b> %{x:.2%}<br>'
                    +'<b>Return:</b> %{y:.2%}'
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

        // 現在の制約を取得
        const currentConstraints = {};
        selectedTickers.forEach(ticker => {
            const minInput = constraintInputsDiv.querySelector(`input.constraint-min[data-ticker="${ticker}"]`);
            const maxInput = constraintInputsDiv.querySelector(`input.constraint-max[data-ticker="${ticker}"]`);
            if (minInput && maxInput) {
                currentConstraints[ticker] = {
                    min: parseFloat(minInput.value),
                    max: parseFloat(maxInput.value)
                };
            }
        });

        try {
            const response = await fetch('/optimize_by_return', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    target_value: targetReturn,
                    period: period,
                    constraints: currentConstraints
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
                <p><strong>Sortino Ratio:</strong> ${result.SortinoRatio.toFixed(2)}</p>
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
                    '<b>Optimized by Return</b><br>'
                    +'<b>Risk:</b> %{x:.2%}<br>'
                    +'<b>Return:</b> %{y:.2%}'
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

        // 現在の制約を取得
        const currentConstraints = {};
        selectedTickers.forEach(ticker => {
            const minInput = constraintInputsDiv.querySelector(`input.constraint-min[data-ticker="${ticker}"]`);
            const maxInput = constraintInputsDiv.querySelector(`input.constraint-max[data-ticker="${ticker}"]`);
            if (minInput && maxInput) {
                currentConstraints[ticker] = {
                    min: parseFloat(minInput.value),
                    max: parseFloat(maxInput.value)
                };
            }
        });

        try {
            const response = await fetch('/optimize_by_risk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    target_value: targetRisk,
                    period: period,
                    constraints: currentConstraints
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
                <p><strong>Sortino Ratio:</strong> ${result.SortinoRatio.toFixed(2)}</p>
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
                    '<b>Optimized by Risk</b><br>'
                    +'<b>Risk:</b> %{x:.2%}<br>'
                    +'<b>Return:</b> %{y:.2%}'
            });

            Plotly.react('graph', updatedData, graphDiv.layout);

        } catch (error) {
            console.error('Error optimizing by risk:', error);
            targetOptimizationResultDiv.innerHTML = '<p style="color: red;">An error occurred while optimizing by risk.</p>';
        }
    });

    // Show Historical Performanceボタンのイベントリスナー
    showHistoricalPerformanceBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF to show historical performance.');
            historicalPerformanceGraphDiv.innerHTML = '';
            return;
        }

        const period = dataPeriodSelect.value;

        try {
            const response = await fetch('/historical_performance', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    period: period
                })
            });
            const historicalData = await response.json();

            if (historicalData.error) {
                historicalPerformanceGraphDiv.innerHTML = `<p style="color: red;">Error: ${historicalData.error}</p>`;
                return;
            }

            const traces = [];
            for (const ticker in historicalData.cumulative_returns) {
                traces.push({
                    x: historicalData.dates,
                    y: historicalData.cumulative_returns[ticker],
                    mode: 'lines',
                    name: ticker,
                    hovertemplate:
                        '<b>Date:</b> %{x}<br>'
                        +'<b>Cumulative Return:</b> %{y:.2%}'
                });
            }

            const layout = {
                title: 'Cumulative Historical Performance',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Cumulative Return' }
            };

            Plotly.newPlot('historical-performance-graph', traces, layout);

        } catch (error) {
            console.error('Error fetching historical performance:', error);
            historicalPerformanceGraphDiv.innerHTML = '<p style="color: red;">An error occurred while fetching historical performance.</p>';
        }
    });

    // Run Monte Carlo Simulationボタンのイベントリスナー
    runMonteCarloBtn.addEventListener('click', async () => {
        const selectedTickers = Array.from(etfCheckboxesDiv.querySelectorAll('input[type="checkbox"]:checked'))
                                    .map(checkbox => checkbox.value);

        if (selectedTickers.length === 0) {
            alert('Please select at least one ETF to run Monte Carlo simulation.');
            monteCarloGraphDiv.innerHTML = '';
            monteCarloResultsDiv.innerHTML = '';
            return;
        }

        const period = dataPeriodSelect.value;
        const numSimulations = parseInt(numSimulationsInput.value);
        const simulationDays = parseInt(simulationDaysInput.value);

        if (isNaN(numSimulations) || isNaN(simulationDays) || numSimulations <= 0 || simulationDays <= 0) {
            alert('Please enter valid positive numbers for simulations and days.');
            return;
        }

        try {
            const response = await fetch('/monte_carlo_simulation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tickers: selectedTickers,
                    period: period,
                    num_simulations: numSimulations,
                    simulation_days: simulationDays
                })
            });
            const simulationResults = await response.json();

            if (simulationResults.error) {
                monteCarloResultsDiv.innerHTML = `<p style="color: red;">Error: ${simulationResults.error}</p>`;
                return;
            }

            const finalReturns = simulationResults.final_returns;

            // ヒストグラムのプロット
            const trace = {
                x: finalReturns.map(r => r * 100), // パーセンテージに変換
                type: 'histogram',
                marker: { color: 'rgba(100, 149, 237, 0.7)' }
            };

            const layout = {
                title: 'Monte Carlo Simulation: Distribution of Final Returns',
                xaxis: { title: 'Final Return (%)' },
                yaxis: { title: 'Frequency' }
            };

            Plotly.newPlot('monte-carlo-graph', [trace], layout);

            // 統計情報の表示
            const meanReturn = (finalReturns.reduce((a, b) => a + b, 0) / finalReturns.length) * 100;
            const sortedReturns = [...finalReturns].sort((a, b) => a - b);
            const percentile5 = sortedReturns[Math.floor(0.05 * sortedReturns.length)] * 100;
            const percentile95 = sortedReturns[Math.floor(0.95 * sortedReturns.length)] * 100;

            const var95 = simulationResults.var_95 * 100;
            const cvar95 = simulationResults.cvar_95 * 100;

            monteCarloResultsDiv.innerHTML = `
                <h3>Simulation Results</h3>
                <p><strong>Mean Final Return:</strong> ${meanReturn.toFixed(2)}%</p>
                <p><strong>5th Percentile Return:</strong> ${percentile5.toFixed(2)}%</p>
                <p><strong>95th Percentile Return:</strong> ${percentile95.toFixed(2)}%</p>
                <p><strong>VaR (95%):</strong> ${var95.toFixed(2)}%</p>
                <p><strong>CVaR (95%):</strong> ${cvar95.toFixed(2)}%</p>
                <p>This simulation assumes historical volatility and correlations remain constant.</p>
            `;

        } catch (error) {
            console.error('Error running Monte Carlo simulation:', error);
            monteCarloResultsDiv.innerHTML = '<p style="color: red;">An error occurred while running the simulation.</p>';
        }
    });

    // Analyze CSVボタンのイベントリスナー
    analyzeCsvBtn.addEventListener('click', () => {
        const file = csvFileInput.files[0];
        if (!file) {
            alert('Please select a CSV file to analyze.');
            return;
        }

        const reader = new FileReader();
        reader.onload = async (e) => {
            const csvContent = e.target.result;
            try {
                const response = await fetch('/analyze_csv_data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ csv_data: csvContent })
                });
                const etfData = await response.json();

                if (etfData.error) {
                    csvAnalysisResultsDiv.innerHTML = `<p style="color: red;">Error: ${etfData.error}</p>`;
                    return;
                }

                // 結果を表示
                let resultsHtml = '<h3>Analysis Results from CSV</h3><table><thead><tr><th>Ticker</th><th>Return</th><th>Risk</th></tr></thead><tbody>';
                etfData.forEach(item => {
                    resultsHtml += `<tr><td>${item.Ticker}</td><td>${(item.Return * 100).toFixed(2)}%</td><td>${(item.Risk * 100).toFixed(2)}%</td></tr>`;
                });
                resultsHtml += '</tbody></table>';
                csvAnalysisResultsDiv.innerHTML = resultsHtml;

                // メイングラフにプロット
                const graphDiv = document.getElementById('graph');
                const currentData = graphDiv.data || [];

                // 既存のCSVからのプロットを削除（もしあれば）
                const updatedData = currentData.filter(trace => trace.name !== 'ETFs from CSV');

                updatedData.push({
                    x: etfData.map(item => item.Risk),
                    y: etfData.map(item => item.Return),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'ETFs from CSV',
                    text: etfData.map(item => item.Ticker),
                    textposition: 'top center',
                    marker: { size: 12, color: 'purple' },
                    hovertemplate:
                        '<b>%{text}</b><br>'
                        +'<b>Risk:</b> %{x:.2%}<br>'
                        +'<b>Return:</b> %{y:.2%}'
                });

                Plotly.react('graph', updatedData, graphDiv.layout);

            } catch (error) {
                console.error('Error analyzing CSV data:', error);
                csvAnalysisResultsDiv.innerHTML = '<p style="color: red;">An error occurred while analyzing CSV data.</p>';
            }
        };
        reader.readAsText(file);
    });

    function generateMap(callback) {
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
        currentWeights = {}; // グローバル変数をリセット

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

        // ETF制約入力フィールドを生成
        constraintInputsDiv.innerHTML = ''; // 既存の制約入力をクリア
        const etfConstraints = {}; // グローバルまたは適切なスコープで定義

        selectedTickers.forEach(ticker => {
            const constraintRow = document.createElement('div');
            constraintRow.style.marginBottom = '5px';
            constraintRow.innerHTML = `
                <label>${ticker}:</label>
                Min: <input type="number" class="constraint-min" data-ticker="${ticker}" value="0" min="0" max="100" step="0.01" style="width: 60px;">
                Max: <input type="number" class="constraint-max" data-ticker="${ticker}" value="100" min="0" max="100" step="0.01" style="width: 60px;">
            `;
            constraintInputsDiv.appendChild(constraintRow);
            etfConstraints[ticker] = { min: 0, max: 100 }; // 初期値
        });

        // 制約入力フィールドのイベントリスナーを設定
        constraintInputsDiv.querySelectorAll('input[type="number"]').forEach(input => {
            input.onchange = (event) => {
                const ticker = event.target.dataset.ticker;
                const value = parseFloat(event.target.value);
                if (event.target.classList.contains('constraint-min')) {
                    etfConstraints[ticker].min = value;
                } else if (event.target.classList.contains('constraint-max')) {
                    etfConstraints[ticker].max = value;
                }
            };
        });

        // 初期表示時にカスタムポートフォリオの結果をクリア
        customPortfolioResultDiv.innerHTML = '';

        const queryParams = new URLSearchParams();
        selectedTickers.forEach(ticker => queryParams.append('tickers', ticker));
        const period = dataPeriodSelect.value;
        queryParams.append('period', period);
        queryParams.append('constraints', JSON.stringify(etfConstraints));

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
                    '<b>%{text}</b><br>'
                    +'<b>Risk:</b> %{x:.2%}<br>'
                    +'<b>Return:</b> %{y:.2%}'
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
                    '<b>Risk:</b> %{x:.2%}<br>'
                    +'<b>Return:</b> %{y:.2%}'
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
                    '<b>Risk-Free Rate</b><br>'
                    +'<b>Return:</b> %{y:.2%}'
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
                        '<b>Capital Market Line</b><br>'
                        +'<b>Risk:</b> %{x:.2%}<br>'
                        +'<b>Return:</b> %{y:.2%}'
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
                        '<b>Max Sharpe Ratio Portfolio</b><br>'
                        +'<b>Risk:</b> %{x:.2%}<br>'
                        +'<b>Return:</b> %{y:.2%}<br>'
                        +'<b>Sharpe Ratio:</b> %{customdata:.2f}'
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
        .catch(error => console.error('Error fetching data:', error))
        .finally(() => {
            // After everything, execute the callback if it was provided
            if (callback && typeof callback === 'function') {
                callback();
            }
        });
    }
});