# ブラウザテスト完全ガイド - アフィリエイト機能

## 📋 テスト前の準備

### 1. アプリケーション起動
```bash
# ターミナル1: FastAPIサーバー起動
python main.py

# 起動確認
# ✅ "Uvicorn running on http://0.0.0.0:8000" が表示される
```

### 2. ブラウザの開発者ツールを開く
- **Chrome/Edge**: F12 または Ctrl+Shift+I
- **Firefox**: F12
- **Safari**: Cmd+Option+I

### 3. 開発者ツールのタブ確認
- ✅ **Console**: JavaScriptエラー確認用
- ✅ **Network**: APIリクエスト確認用
- ✅ **Application** (Chrome) / **Storage** (Firefox): Cookie/localStorage確認用

---

## 🧪 テストシナリオ 1: 証券会社比較ページ

### URL: http://localhost:8000/brokers

### テスト項目

#### ✅ 1.1 ページが正常に表示される

**確認方法:**
1. ブラウザで http://localhost:8000/brokers にアクセス
2. ページが読み込まれることを確認

**期待される表示:**
- ヘッダーに「ETF投資におすすめの証券会社」
- 地域タブ（米国 / 日本 / グローバル）
- 証券会社カードが6枚表示される

**開発者ツールでの確認:**
```
Console タブ:
- エラーがないことを確認
- 赤いエラーメッセージがないこと
```

**NGの場合:**
```
Console に以下のようなエラーが出る場合:
❌ "Failed to load resource: brokers.js"
   → static/brokers.js が存在するか確認

❌ "Uncaught ReferenceError: loadBrokers is not defined"
   → brokers.js が正しく読み込まれているか確認
```

---

#### ✅ 1.2 地域フィルタが動作する

**手順:**
1. 「米国」タブをクリック
2. 表示される証券会社を確認
3. 「日本」タブをクリック
4. 表示される証券会社を確認

**期待される動作:**
- **米国タブ**: Interactive Brokers, Charles Schwab, Fidelity のみ表示
- **日本タブ**: 楽天証券, SBI証券, マネックス証券 のみ表示

**開発者ツールでの確認:**
```
Network タブ:
1. 「米国」タブをクリック
2. 以下のリクエストが送信されることを確認:
   GET /api/brokers?region=US

3. Responseを確認:
   {
     "brokers": [
       {"broker_name": "interactive_brokers", ...},
       {"broker_name": "charles_schwab", ...},
       {"broker_name": "fidelity", ...}
     ]
   }
```

**NGの場合:**
```javascript
// Console で手動実行してテスト
filterByRegion('US');

// エラーが出る場合は brokers.js を確認
```

---

#### ✅ 1.3 アフィリエイトリンクがクリック可能

**手順:**
1. 任意の証券会社カードの「無料で口座開設」ボタンをクリック
2. クリックイベントが発火することを確認

**開発者ツールでの確認:**

**Network タブ:**
```
ボタンをクリック後、以下のリクエストが送信されるか確認:

POST /api/brokers/track-click

Request Payload:
{
  "broker_id": 1,
  "placement": "broker_page",
  "portfolio_data": null
}

Response:
{
  "success": true,
  "click_id": 1,
  "redirect_url": "https://ibkr.com/referral/placeholder"
}
```

**Console タブ:**
```
Google Analyticsイベントが送信されているか確認:

✅ 以下のようなログが出れば成功:
   "GA4 Event: affiliate_click"
   または
   dataLayer に push されている
```

**データベースでの確認:**
```bash
# 別ターミナルで実行
sqlite3 data/affiliate.db "SELECT broker_id, placement, clicked_at FROM affiliate_clicks ORDER BY clicked_at DESC LIMIT 5;"

# 期待される出力:
# 最新のクリックレコードが表示される
# 1|broker_page|2025-01-15 10:30:00
```

**NGの場合:**
```javascript
// Console で手動テスト
trackAffiliateClick(1, 'broker_page', null);

// エラーが出る場合:
// ❌ "trackAffiliateClick is not defined"
//    → analytics.js が正しくインポートされているか確認
```

---

#### ✅ 1.4 "AD"バッジが表示される

**確認方法:**
1. 各証券会社カードの「無料で口座開設」ボタンの近くを確認
2. "AD" または "広告" のバッジが表示されているか

**期待される表示:**
```html
<span class="badge bg-info">AD</span>
```

**NGの場合:**
- brokers.html のテンプレートを確認
- CSS が正しく読み込まれているか確認

---

## 🧪 テストシナリオ 2: メインページのブローカー推薦

### URL: http://localhost:8000

### テスト項目

#### ✅ 2.1 ポートフォリオ分析後に推薦が表示される

**手順:**
1. http://localhost:8000 にアクセス
2. サイドバーから適当なETFを2-3個選択（例: VTI, BND, GLD）
3. 「Generate Map」ボタンをクリック
4. 分析結果の下にスクロール

**期待される表示:**
```
🚀 このポートフォリオを実際に運用する

分析したポートフォリオを実際に投資してみませんか？

[証券会社カード3枚]
- Interactive Brokers (または楽天証券、地域による)
- Charles Schwab (またはSBI証券)
- Fidelity (またはマネックス証券)
```

**開発者ツールでの確認:**

**Network タブ:**
```
1. Generate Mapをクリック後、以下のリクエストを確認:

GET /portfolio/efficient_frontier?tickers=VTI&tickers=BND&period=5y

2. その後、以下のリクエストが自動的に送信される:

GET /api/brokers/recommend?region=US&etfs=VTI&etfs=BND

3. Response を確認:
{
  "brokers": [
    {"broker_id": 1, "display_name": "Interactive Brokers", ...},
    {"broker_id": 2, "display_name": "Charles Schwab", ...},
    {"broker_id": 3, "display_name": "Fidelity", ...}
  ]
}
```

**Console タブ:**
```
✅ エラーがないことを確認
✅ 以下のようなログが出れば成功:
   "Broker recommendations loaded: 3"
```

**NGの場合:**
```javascript
// Console で手動実行
showBrokerRecommendations(['VTI', 'BND']);

// エラーメッセージを確認:
// ❌ "getBrokerRecommendations is not defined"
//    → api.js に関数が定義されているか確認

// ❌ "displayBrokerRecommendations is not defined"
//    → ui.js に関数が定義されているか確認
```

---

#### ✅ 2.2 地域が自動判定される

**確認方法:**
```javascript
// Console で実行
console.log(navigator.language);

// 期待される動作:
// "ja" または "ja-JP" → 日本の証券会社が表示される
// "en" または "en-US" → 米国の証券会社が表示される
```

**手動テスト:**
```javascript
// Console で地域を強制変更してテスト
const response = await fetch('/api/brokers/recommend?region=JP');
const data = await response.json();
console.log(data.brokers);

// 楽天証券、SBI証券、マネックス証券が返ってくるか確認
```

---

#### ✅ 2.3 クリック追跡が動作する

**手順:**
1. ブローカー推薦カードの「無料で口座開設」ボタンをクリック
2. クリックが記録されることを確認

**開発者ツールでの確認:**

**Network タブ:**
```
POST /api/brokers/track-click

Request Payload:
{
  "broker_id": 1,
  "placement": "portfolio_result",
  "portfolio_data": {
    "tickers": ["VTI", "BND"],
    "weights": {"VTI": 0.6, "BND": 0.4}
  }
}
```

**Console タブ:**
```
✅ Google Analytics イベントが送信される:
   dataLayer に以下が push される:
   {
     event: 'affiliate_click',
     broker_name: 'interactive_brokers',
     placement: 'portfolio_result'
   }
```

---

## 🧪 テストシナリオ 3: 管理者ダッシュボード

### URL: http://localhost:8000/admin/affiliate

### ⚠️ 注意: 認証について

現在、管理者認証が実装されている場合、以下の一時的な対応が必要です:

**Option A: 認証を一時的にバイパス**
```python
# app/api/admin.py を編集
@router.get("/affiliate/stats")
async def get_affiliate_stats(
    # 以下の行をコメントアウト
    # current_user: User = Depends(get_admin_user),
    start_date: str = None,
    end_date: str = None
):
    # ...
```

**Option B: ログインしてテスト**
- メインページでログイン
- 管理者権限があることを確認

---

### テスト項目

#### ✅ 3.1 ダッシュボードが表示される

**確認方法:**
1. http://localhost:8000/admin/affiliate にアクセス
2. ページが読み込まれることを確認

**期待される表示:**
- サマリーカード: 総クリック数、総コンバージョン数、転換率、推定収益
- 期間選択ドロップダウン
- グラフエリア（3つ）
- データテーブル

**開発者ツールでの確認:**

**Network タブ:**
```
GET /api/admin/affiliate/stats?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

Response:
{
  "period": {"start": "...", "end": "..."},
  "total_clicks": 5,
  "total_conversions": 0,
  "conversion_rate": 0,
  "estimated_revenue": 0,
  "by_broker": [...],
  "by_placement": [...]
}
```

**Console タブ:**
```
✅ Chart.js が読み込まれているか確認:
typeof Chart

// "function" が返ってくればOK
```

---

#### ✅ 3.2 Chart.jsのグラフが描画される

**確認方法:**
1. ページをスクロールしてグラフエリアを確認
2. 以下の3つのグラフが表示されるか確認:
   - クリック数の推移（折れ線グラフ）
   - 証券会社別パフォーマンス（棒グラフ）
   - 配置別クリック数（円グラフ）

**開発者ツールでの確認:**

**Console タブ:**
```javascript
// 手動でグラフが存在するか確認
document.getElementById('clicks-chart');
document.getElementById('broker-performance-chart');
document.getElementById('placement-chart');

// null でなければグラフエリアは存在する
```

**NGの場合:**
```javascript
// Console で手動テスト
// Chart.js が読み込まれているか確認
console.log(typeof Chart);

// "undefined" の場合:
// ❌ Chart.js が読み込まれていない
//    → affiliate_dashboard.html を確認
//    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

**データがない場合:**
- グラフは表示されるが、データポイントがない状態
- これは正常（まだクリックデータがないため）
- テストデータを追加:

```bash
sqlite3 data/affiliate.db
```

```sql
-- テストクリックを追加
INSERT INTO affiliate_clicks (broker_id, session_id, placement, clicked_at)
VALUES 
  (1, 'test-session-1', 'portfolio_result', datetime('now')),
  (1, 'test-session-2', 'broker_page', datetime('now', '-1 day')),
  (2, 'test-session-3', 'portfolio_result', datetime('now', '-2 days'));
```

ページをリロードしてグラフが更新されるか確認。

---

#### ✅ 3.3 期間選択が動作する

**手順:**
1. 期間選択ドロップダウンをクリック
2. 「過去7日」「過去30日」などを選択
3. データが更新されることを確認

**開発者ツールでの確認:**

**Network タブ:**
```
期間を変更すると新しいリクエストが送信される:

GET /api/admin/affiliate/stats?start_date=2025-01-08&end_date=2025-01-15
```

---

## 🧪 テストシナリオ 4: Google Analytics統合

### テスト項目

#### ✅ 4.1 GA4が正しく読み込まれている

**確認方法:**

**Console タブ:**
```javascript
// gtag関数が存在するか確認
typeof gtag

// "function" が返ってくればOK

// dataLayerが存在するか確認
window.dataLayer

// 配列が返ってくればOK
```

**Network タブ:**
```
ページ読み込み時に以下のリクエストが送信される:

GET https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX

Status: 200 OK
```

**NGの場合:**
```
❌ "gtag is not defined"
   → index.html の <head> にGA4スクリプトが含まれているか確認

❌ "Failed to load resource: gtag/js"
   → インターネット接続を確認
   → 測定ID（G-XXXXXXXXXX）が正しいか確認
```

---

#### ✅ 4.2 クリックイベントが送信される

**手順:**
1. ブローカーリンクをクリック
2. イベントが送信されることを確認

**開発者ツールでの確認:**

**Console タブ:**
```javascript
// dataLayerの内容を確認
console.log(window.dataLayer);

// 期待される内容:
[
  {...},  // 初期化データ
  {
    event: 'affiliate_click',
    broker_name: 'interactive_brokers',
    broker_region: 'US',
    placement: 'portfolio_result',
    ...
  }
]
```

**Network タブ:**
```
クリック後、以下のようなリクエストが送信される:

POST https://www.google-analytics.com/g/collect?v=2&...

Query Parameters に以下が含まれる:
- en: affiliate_click (event name)
- ep.broker_name: interactive_brokers
```

---

#### ✅ 4.3 ポートフォリオ作成イベントが送信される

**手順:**
1. ポートフォリオを作成（Generate Mapをクリック）
2. イベントが送信されることを確認

**開発者ツールでの確認:**

**Console タブ:**
```javascript
window.dataLayer.filter(item => item.event === 'portfolio_created');

// 期待される結果:
[
  {
    event: 'portfolio_created',
    num_etfs: 3,
    event_category: 'engagement'
  }
]
```

---

## 🧪 テストシナリオ 5: ダークモード

### テスト項目

#### ✅ 5.1 ダークモード切り替えが動作する

**手順:**
1. ナビゲーションバーの右上にあるテーマトグルボタンをクリック
2. ページの背景色とテキスト色が変わることを確認
3. もう一度クリックして元に戻ることを確認

**期待される動作:**
- ライトモード → ダークモード: 背景が暗くなる
- ダークモード → ライトモード: 背景が明るくなる
- localStorageに設定が保存される

**開発者ツールでの確認:**

**Application タブ (Chrome) / Storage タブ (Firefox):**
```
Local Storage → http://localhost:8000

Key: theme
Value: "dark" または "light"
```

**Console タブ:**
```javascript
// 手動でテーマを確認
localStorage.getItem('theme');

// "dark" または "light" が返ってくる
```

---

#### ✅ 5.2 証券会社比較ページでもダークモードが動作

**手順:**
1. ダークモードを有効にする
2. /brokers ページに移動
3. ダークモードが保持されているか確認

---

## 📊 総合テスト結果の記録

以下のフォーマットでテスト結果を記録してください:

```markdown
## テスト実施日: 2025-01-XX

### シナリオ1: 証券会社比較ページ
- [ ] 1.1 ページ表示: ✅ / ❌
- [ ] 1.2 地域フィルタ: ✅ / ❌
- [ ] 1.3 アフィリエイトリンク: ✅ / ❌
- [ ] 1.4 ADバッジ: ✅ / ❌

### シナリオ2: ブローカー推薦
- [ ] 2.1 推薦表示: ✅ / ❌
- [ ] 2.2 地域自動判定: ✅ / ❌
- [ ] 2.3 クリック追跡: ✅ / ❌

### シナリオ3: 管理者ダッシュボード
- [ ] 3.1 ダッシュボード表示: ✅ / ❌
- [ ] 3.2 グラフ描画: ✅ / ❌
- [ ] 3.3 期間選択: ✅ / ❌

### シナリオ4: Google Analytics
- [ ] 4.1 GA4読み込み: ✅ / ❌
- [ ] 4.2 クリックイベント: ✅ / ❌
- [ ] 4.3 ポートフォリオイベント: ✅ / ❌

### シナリオ5: ダークモード
- [ ] 5.1 切り替え動作: ✅ / ❌
- [ ] 5.2 ページ間保持: ✅ / ❌

### 問題・エラー
記述してください...
```

---

## 🆘 よくある問題と解決策

### 問題1: NetworkエラーでAPIリクエストが失敗

**症状:**
```
Console:
Failed to fetch
net::ERR_CONNECTION_REFUSED
```

**解決策:**
```bash
# FastAPIサーバーが起動しているか確認
ps aux | grep python

# 起動していない場合
python main.py
```

---

### 問題2: 証券会社カードが表示されない

**確認ポイント:**
1. データベースにデータが存在するか
```bash
sqlite3 data/affiliate.db "SELECT COUNT(*) FROM affiliate_brokers;"
# 6 が返ってくるはず
```

2. APIレスポンスを確認
```javascript
// Console で実行
fetch('/api/brokers')
  .then(r => r.json())
  .then(console.log);
```

---

### 問題3: グラフが表示されない

**確認ポイント:**
1. Chart.jsが読み込まれているか
```javascript
typeof Chart
// "function" が返ってくるはず
```

2. Canvas要素が存在するか
```javascript
document.getElementById('clicks-chart')
// <canvas> が返ってくるはず
```

3. テストデータを追加してリロード

---

### 問題4: Google Analyticsイベントが送信されない

**確認ポイント:**
1. 測定IDが正しいか
```html
<!-- index.html -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

2. analytics.jsが読み込まれているか
```javascript
// Console で確認
typeof trackAffiliateClick
// "function" が返ってくるはず
```

---

## ✅ 完了基準

すべてのシナリオで ✅ がつけば、実装は完全に成功しています！

次のステップ:
1. 証券会社のアフィリエイトプログラムに申請
2. 実際のアフィリエイトURLに更新
3. 最初のブログ記事を作成・公開
4. 本番環境にデプロイ

頑張ってください！ 🚀