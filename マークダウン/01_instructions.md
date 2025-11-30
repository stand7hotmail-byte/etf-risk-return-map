# Gemini CLI 実装指示書 - アフィリエイト機能追加

このドキュメントは、アフィリエイト収益化機能を段階的に実装するための、Gemini CLIへの具体的な指示をまとめたものです。

---

## 📋 使い方

各フェーズごとに、Gemini CLIに**そのままコピー&ペースト**できる指示文を用意しています。

**推奨ワークフロー:**
1. 各指示をコピー
2. Gemini CLIで実行
3. 生成されたコードをレビュー
4. テスト
5. 次のステップへ

---

## 🎯 フェーズ1: データベース基盤（Day 1-2）

### ステップ 1.1: アフィリエイトモデルの作成

```
プロジェクトの既存構造を維持しながら、以下の要件でアフィリエイト管理用のデータベースモデルを作成してください:

【要件】
1. Peewee ORMを使用
2. 以下の2つのモデルを作成:
   - AffiliateBroker: 証券会社情報を管理
   - AffiliateClick: クリックとコンバージョンを追跡

【AffiliateBroker モデルの仕様】
- broker_id: 主キー（自動採番）
- broker_name: 証券会社名（例: "Interactive Brokers"）
- display_name: 表示名（日本語対応）
- region: 地域（US, JP, EU）
- affiliate_url: アフィリエイトリンク
- commission_rate: 報酬額（例: 100.00）
- commission_type: 報酬タイプ（CPA, RevShare）
- logo_url: ロゴ画像のパス
- description: 説明文
- pros: 利点（JSON配列）
- best_for: 最適なユーザータイプ
- rating: 評価（1-5）
- is_active: アクティブフラグ
- created_at, updated_at: タイムスタンプ

【AffiliateClick モデルの仕様】
- click_id: 主キー（自動採番）
- broker_id: 外部キー（AffiliateBroker）
- user_id: 外部キー（User、nullable）
- session_id: セッションID
- clicked_at: クリック日時
- ip_address: IPアドレス
- user_agent: ユーザーエージェント
- referrer: リファラー
- placement: 配置場所（例: "portfolio_result", "broker_page"）
- portfolio_data: 分析していたポートフォリオ（JSON、nullable）
- converted: コンバージョンフラグ
- converted_at: コンバージョン日時（nullable）

【ファイル配置】
- app/models/affiliate.py

【追加要件】
- 既存のデータベース設定（app/config.py）と統合
- マイグレーション用のヘルパー関数も含める
- 型ヒントを使用
- Docstringを追加（Google形式）

参考: 既存のユーザーモデルの実装スタイルに合わせてください。
```

### ステップ 1.2: 初期データのシードスクリプト

```
アフィリエイト証券会社の初期データを登録するシードスクリプトを作成してください。

【要件】
1. 以下の証券会社を登録:

【米国市場】
- Interactive Brokers
  - region: US
  - affiliate_url: "https://ibkr.com/referral/your-id" (プレースホルダー)
  - commission_rate: 200.00
  - commission_type: CPA
  - pros: ["11,000以上のETF手数料無料", "グローバル対応", "API統合可能"]
  - best_for: "中級〜上級投資家、自動化を希望する方"
  - rating: 4.5

- Charles Schwab
  - region: US
  - commission_rate: 100.00
  - pros: ["初心者向けUI", "豊富な教育リソース", "24/7サポート"]
  - best_for: "投資初心者"
  - rating: 4.3

- Fidelity
  - region: US
  - commission_rate: 150.00
  - pros: ["ゼロ手数料ETF多数", "優れたリサーチツール"]
  - best_for: "長期投資家"
  - rating: 4.4

【日本市場】
- 楽天証券
  - region: JP
  - commission_rate: 8000.00 (円)
  - pros: ["楽天ポイント統合", "米国ETF豊富", "使いやすいアプリ"]
  - best_for: "楽天経済圏利用者、投資初心者"
  - rating: 4.6

- SBI証券
  - region: JP
  - commission_rate: 10000.00
  - pros: ["国内最大手", "商品ラインナップ最多", "低コスト"]
  - best_for: "全ての投資家"
  - rating: 4.5

- マネックス証券
  - region: JP
  - commission_rate: 7000.00
  - pros: ["米国株・ETFに強い", "トレーディングツール充実"]
  - best_for: "米国株投資家"
  - rating: 4.3

【ファイル配置】
- scripts/seed_brokers.py

【実行方法】
```bash
python scripts/seed_brokers.py
```

【追加要件】
- 既存データがある場合は更新（upsert）
- 実行結果をログ出力
- エラーハンドリング
```

---

## 🎨 フェーズ2: APIエンドポイント（Day 3-4）

### ステップ 2.1: アフィリエイトAPI基本エンドポイント

```
アフィリエイト証券会社を管理・取得するためのAPIエンドポイントを作成してください。

【要件】
1. FastAPIのルーターを使用
2. 以下のエンドポイントを実装:

【GET /api/brokers】
- 説明: 証券会社一覧を取得
- クエリパラメータ:
  - region: 地域フィルタ（optional, default: all）
  - active_only: アクティブのみ（optional, default: true）
- レスポンス例:
```json
{
  "brokers": [
    {
      "broker_id": 1,
      "broker_name": "interactive_brokers",
      "display_name": "Interactive Brokers",
      "region": "US",
      "affiliate_url": "https://...",
      "logo_url": "/static/images/brokers/ibkr.png",
      "description": "グローバル対応の総合証券会社",
      "pros": ["..."],
      "best_for": "中級〜上級投資家",
      "rating": 4.5
    }
  ]
}
```

【GET /api/brokers/recommend】
- 説明: ユーザーに最適な証券会社を推薦
- クエリパラメータ:
  - region: 地域（required）
  - user_level: 投資家レベル（beginner/intermediate/advanced, optional）
  - etfs: 取引予定のETFティッカー（optional, 複数可）
- ロジック:
  - regionでフィルタ
  - user_levelに基づいてbest_forでマッチング
  - ratingの高い順に最大3件返す
- レスポンス: 上記と同じ形式

【POST /api/brokers/track-click】
- 説明: アフィリエイトリンクのクリックを記録
- リクエストボディ:
```json
{
  "broker_id": 1,
  "placement": "portfolio_result",
  "portfolio_data": {
    "tickers": ["VTI", "BND"],
    "weights": {"VTI": 0.6, "BND": 0.4}
  }
}
```
- 処理:
  - AffiliateClickレコードを作成
  - session_id: リクエストからCookieまたはヘッダーで取得
  - user_id: 認証済みユーザーの場合のみ記録
  - ip_address, user_agent: リクエストから抽出
- レスポンス:
```json
{
  "success": true,
  "click_id": 123,
  "redirect_url": "https://ibkr.com/referral/..."
}
```

【ファイル配置】
- app/api/affiliate.py

【追加要件】
- Pydanticスキーマを定義（app/schemas.py に追加）
- エラーハンドリング（404, 400）
- レート制限を考慮（slowapi）
- 既存のAPIルーターに統合（app/main.py）
- OpenAPI docstringを追加
```

### ステップ 2.2: アナリティクスエンドポイント（管理者用）

```
アフィリエイトのパフォーマンスを分析するための管理者用エンドポイントを作成してください。

【要件】
1. 認証必須（管理者権限チェック）
2. 以下のエンドポイントを実装:

【GET /api/admin/affiliate/stats】
- 説明: 全体の統計情報を取得
- クエリパラメータ:
  - start_date: 集計開始日（optional, default: 30日前）
  - end_date: 集計終了日（optional, default: 今日）
- レスポンス:
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "total_clicks": 1234,
  "total_conversions": 45,
  "conversion_rate": 3.65,
  "estimated_revenue": 6750.00,
  "by_broker": [
    {
      "broker_name": "Interactive Brokers",
      "clicks": 500,
      "conversions": 20,
      "conversion_rate": 4.0,
      "revenue": 4000.00
    }
  ],
  "by_placement": [
    {
      "placement": "portfolio_result",
      "clicks": 800,
      "conversions": 35,
      "conversion_rate": 4.38
    }
  ]
}
```

【GET /api/admin/affiliate/top-performing】
- 説明: 最もパフォーマンスの良い証券会社を取得
- クエリパラメータ:
  - metric: ランキング基準（clicks/conversions/revenue, default: conversions）
  - limit: 取得件数（default: 5）
- レスポンス: broker情報 + 統計

【POST /api/admin/affiliate/conversions】
- 説明: コンバージョン（口座開設）を手動で記録
- リクエストボディ:
```json
{
  "click_id": 123,
  "converted_at": "2025-01-15T10:30:00Z"
}
```
- 処理: AffiliateClickのconvertedをtrueに更新

【ファイル配置】
- app/api/admin.py（既存ファイルがあれば統合）

【追加要件】
- 管理者認証ミドルウェア（既存のauth実装を参照）
- SQLクエリの最適化（集計にindexを活用）
- キャッシング（1時間TTL）
```

---

## 💻 フェーズ3: フロントエンド実装（Day 5-7）

### ステップ 3.1: 証券会社比較ページ

```
証券会社を比較・選択できるWebページを作成してください。

【要件】
1. 新規HTMLページ: templates/brokers.html
2. 対応するJavaScriptモジュール: static/brokers.js

【HTMLの要件】
- 既存のindex.htmlと同じデザインシステム（Bootstrap 5）を使用
- ヘッダー・フッターは共通化
- レスポンシブデザイン

【ページ構成】
1. ヒーローセクション
   - タイトル: "ETF投資におすすめの証券会社"
   - サブタイトル: "あなたに最適な証券会社を見つけよう"

2. 地域選択タブ
   - 米国 / 日本 / グローバル
   - タブ切り替えで表示内容を変更

3. 証券会社カード（各社）
   - ロゴ画像
   - 会社名
   - 評価（星マーク）
   - 利点のリスト（チェックマーク付き）
   - "最適な人: XXX"
   - CTAボタン: "無料で口座開設"（アフィリエイトリンク）
   - "AD"バッジ（アフィリエイト開示）

4. 比較表
   - 横スクロール可能なテーブル
   - 列: 証券会社 / 手数料 / ETF数 / 最低投資額 / 特徴
   - ソート機能（JavaScript）

5. FAQ セクション
   - "どの証券会社を選べばいい？"
   - "口座開設にかかる時間は？"
   - "複数の証券会社を使っていい？"

【JavaScriptの要件（brokers.js）】
```javascript
// 実装する機能
export async function loadBrokers(region = 'all') {
  // GET /api/brokers から取得
  // カードを動的に生成
}

export function filterByRegion(region) {
  // タブ切り替え時の処理
}

export function sortBrokersBy(criteria) {
  // 比較表のソート
}

export function trackAffiliateClick(brokerId, placement) {
  // POST /api/brokers/track-click
  // クリック後にアフィリエイトURLへリダイレクト
}

document.addEventListener('DOMContentLoaded', () => {
  loadBrokers('US');
  setupEventListeners();
});
```

【ルーティング追加（main.py）】
```python
@app.get("/brokers", response_class=HTMLResponse)
async def brokers_page(request: Request):
    return templates.TemplateResponse("brokers.html", {"request": request})
```

【追加要件】
- ダークモード対応（既存のtheme.js統合）
- ローディングスピナー
- エラーハンドリング（APIが失敗した場合）
- アクセシビリティ（ARIA属性）
- SEO最適化（meta tags）
```

### ステップ 3.2: ポートフォリオ結果への証券会社提案の追加

```
既存のポートフォリオ分析結果画面に、証券会社への自然な導線を追加してください。

【要件】
1. 修正ファイル: 
   - templates/index.html
   - static/main.js
   - static/ui.js

【表示タイミング】
- ユーザーがポートフォリオを作成・分析した直後
- "Max Sharpe Ratio Portfolio Composition"の下に表示

【UIコンポーネント（HTML追加部分）】
```html
<!-- portfolio-composition の後に追加 -->
<div id="broker-recommendation" class="card mt-4 border-primary" style="display: none;">
  <div class="card-header bg-primary text-white">
    <h5 class="mb-0">
      <i class="bi bi-rocket-takeoff me-2"></i>
      このポートフォリオを実際に運用する
    </h5>
  </div>
  <div class="card-body">
    <p class="lead">
      分析したポートフォリオを実際に投資してみませんか？
    </p>
    <p class="text-muted small">
      以下の証券会社では、選択したETFを低コストで取引できます。
    </p>
    
    <div id="recommended-brokers-list" class="row">
      <!-- JavaScriptで動的に生成 -->
    </div>
    
    <hr>
    <p class="text-muted small mb-0">
      <i class="bi bi-info-circle me-1"></i>
      これらは当サイトが提携する証券会社です。口座開設により当サイトに報酬が発生する場合がありますが、
      あなたに追加費用は一切かかりません。
    </p>
  </div>
</div>
```

【JavaScript実装（main.jsに追加）】
```javascript
// ポートフォリオ生成成功時に呼び出す
async function showBrokerRecommendations(selectedTickers) {
  try {
    const response = await api.getBrokerRecommendations({
      region: detectUserRegion(), // navigator.languageから判定
      etfs: selectedTickers
    });
    
    ui.displayBrokerRecommendations(response.brokers);
    document.getElementById('broker-recommendation').style.display = 'block';
    
  } catch (error) {
    console.error('Failed to load broker recommendations:', error);
  }
}

// generateMap()関数の成功コールバックに追加
```

【ui.jsに追加する関数】
```javascript
export function displayBrokerRecommendations(brokers) {
  const container = document.getElementById('recommended-brokers-list');
  container.innerHTML = '';
  
  brokers.slice(0, 3).forEach(broker => {
    const card = createBrokerCard(broker);
    container.appendChild(card);
  });
}

function createBrokerCard(broker) {
  // Bootstrap cardを生成
  // ロゴ、評価、利点リスト、CTAボタンを含む
  // ボタンクリック時にtrackAffiliateClick()を呼び出す
}
```

【api.jsに追加する関数】
```javascript
export async function getBrokerRecommendations(params) {
  const query = new URLSearchParams(params);
  const response = await fetch(`/api/brokers/recommend?${query}`);
  if (!response.ok) throw new Error('Failed to fetch recommendations');
  return response.json();
}

export async function trackBrokerClick(brokerId, placement, portfolioData) {
  return post('/api/brokers/track-click', {
    broker_id: brokerId,
    placement: placement,
    portfolio_data: portfolioData
  });
}
```

【追加要件】
- アニメーション効果（fade-in）
- A/Bテスト用のdata属性（後で使用）
- Google Analytics統合準備
```

### ステップ 3.3: ナビゲーションメニューへの追加

```
既存のナビゲーションバーに"証券会社比較"リンクを追加してください。

【要件】
1. 修正ファイル: templates/index.html

【追加箇所】
- ナビゲーションバーの右側
- "ETF Risk-Return Map"の隣

【HTMLコード】
```html
<nav class="navbar navbar-expand-lg bg-dark navbar-dark shadow-sm">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">
      <i class="bi bi-bullseye me-2"></i>ETF Risk-Return Map
    </a>
    
    <!-- 追加部分 -->
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" 
            data-bs-target="#navbarNav">
      <span class="navbar-toggler-icon"></span>
    </button>
    
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav me-auto">
        <li class="nav-item">
          <a class="nav-link" href="/brokers">
            <i class="bi bi-bank me-1"></i>証券会社比較
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link" href="/docs" target="_blank">
            <i class="bi bi-file-text me-1"></i>API Docs
          </a>
        </li>
      </ul>
      
      <div class="d-flex ms-auto align-items-center">
        <!-- 既存のテーマトグル・認証ボタン -->
      </div>
    </div>
  </div>
</nav>
```

【レスポンシブ対応】
- モバイルではハンバーガーメニュー
- タブレット以上では横並び

【アクティブ状態の表示】
- 現在のページに応じて`.active`クラスを付与
```

---

## 📊 フェーズ4: アナリティクス実装（Day 8-9）

### ステップ 4.1: トラッキングダッシュボード

```
管理者向けのアフィリエイトパフォーマンスダッシュボードを作成してください。

【要件】
1. 新規HTMLページ: templates/admin/affiliate_dashboard.html
2. JavaScriptモジュール: static/admin-dashboard.js

【ページ構成】
1. サマリーカード（上部）
   - 総クリック数
   - 総コンバージョン数
   - 転換率
   - 推定収益

2. 期間選択
   - ドロップダウン: 過去7日 / 30日 / 90日 / カスタム期間

3. グラフセクション
   - クリック数の推移（折れ線グラフ、Chart.js）
   - 証券会社別パフォーマンス（棒グラフ）
   - 配置別クリック数（円グラフ）

4. データテーブル
   - 証券会社ごとの詳細統計
   - ソート・フィルタ機能

【JavaScriptの実装】
```javascript
// static/admin-dashboard.js

async function loadDashboardData(startDate, endDate) {
  const stats = await fetch(`/api/admin/affiliate/stats?start_date=${startDate}&end_date=${endDate}`);
  const data = await stats.json();
  
  updateSummaryCards(data);
  renderClicksChart(data);
  renderBrokerPerformanceChart(data.by_broker);
  renderPlacementChart(data.by_placement);
  populateDataTable(data.by_broker);
}

function updateSummaryCards(data) {
  document.getElementById('total-clicks').textContent = data.total_clicks.toLocaleString();
  document.getElementById('total-conversions').textContent = data.total_conversions;
  document.getElementById('conversion-rate').textContent = data.conversion_rate.toFixed(2) + '%';
  document.getElementById('estimated-revenue').textContent = '$' + data.estimated_revenue.toLocaleString();
}

// Chart.js を使用したグラフ描画関数
```

【ルーティング追加（main.py）】
```python
@app.get("/admin/affiliate", response_class=HTMLResponse)
async def affiliate_dashboard(
    request: Request,
    current_user: User = Depends(get_admin_user)  # 管理者認証
):
    return templates.TemplateResponse(
        "admin/affiliate_dashboard.html",
        {"request": request}
    )
```

【セキュリティ】
- 管理者権限がない場合は403エラー
- CSRFトークンの検証

【追加要件】
- データのエクスポート機能（CSV）
- リアルタイム更新（WebSocket optional）
- レスポンシブデザイン
```

### ステップ 4.2: Google Analytics統合

```
Google Analytics 4（GA4）を統合して、アフィリエイトリンクのクリックを追跡してください。

【要件】
1. GA4タグの実装
2. カスタムイベントの送信
3. コンバージョントラッキング

【index.htmlへの追加（headセクション）】
```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

【イベント送信（api.jsまたは新規ファイル）】
```javascript
// static/analytics.js

export function trackAffiliateClick(broker, placement, portfolioData) {
  // 内部トラッキング
  fetch('/api/brokers/track-click', {
    method: 'POST',
    body: JSON.stringify({
      broker_id: broker.broker_id,
      placement: placement,
      portfolio_data: portfolioData
    })
  });
  
  // Google Analytics
  if (typeof gtag !== 'undefined') {
    gtag('event', 'affiliate_click', {
      'broker_name': broker.broker_name,
      'broker_region': broker.region,
      'placement': placement,
      'commission_rate': broker.commission_rate,
      'event_category': 'affiliate',
      'event_label': `${broker.broker_name}_${placement}`,
      'value': broker.commission_rate
    });
  }
}

export function trackPortfolioCreation(tickers, numTickers) {
  if (typeof gtag !== 'undefined') {
    gtag('event', 'portfolio_created', {
      'num_etfs': numTickers,
      'event_category': 'engagement'
    });
  }
}

export function trackPageView(pageName) {
  if (typeof gtag !== 'undefined') {
    gtag('event', 'page_view', {
      'page_title': pageName,
      'page_location': window.location.href
    });
  }
}
```

【GA4でのコンバージョン設定】
管理画面での手動設定手順をコメントで記載:
```
1. GA4管理画面 > イベント
2. 「affiliate_click」イベントをコンバージョンとしてマーク
3. 目標値: broker.commission_rate
```

【プライバシー対応】
- Cookie同意バナーの実装（GDPR対応）
- オプトアウト機能
```

---

## 📝 フェーズ5: コンテンツ作成（Day 10-14）

### ステップ 5.1: ブログシステムの基礎

```
SEO最適化されたブログ機能を追加してください。

【要件】
1. 静的HTMLでのブログページ生成
2. マークダウンからHTMLへの変換
3. SEOメタタグの自動生成

【ディレクトリ構造】
```
content/
  blog/
    2025-01-15-etf-investing-guide.md
    2025-01-20-how-to-choose-broker.md
    ...
templates/
  blog/
    index.html  # ブログ一覧
    post.html   # 個別記事
```

【マークダウンファイルの形式】
```markdown
---
title: "初心者のためのETF投資ガイド"
slug: "etf-investing-guide"
date: "2025-01-15"
author: "ETF分析チーム"
description: "ETF投資の基礎から実践までを徹底解説。ポートフォリオ構築のコツも紹介。"
tags: ["ETF", "初心者", "投資入門"]
featured_image: "/static/images/blog/etf-guide.jpg"
---

# 初心者のためのETF投資ガイド

ETF（上場投資信託）は、初心者にも取り組みやすい投資商品です。

## ETFとは？

...
```

【Pythonスクリプト（ビルド用）】
```python
# scripts/build_blog.py

import markdown
import yaml
from pathlib import Path
from jinja2 import Template

def parse_markdown_with_frontmatter(filepath):
    """マークダウンファイルをパースしてメタデータとコンテンツを分離"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # FrontMatterとコンテンツを分離
    parts = content.split('---', 2)
    metadata = yaml.safe_load(parts[1])
    markdown_content = parts[2]
    
    # マークダウンをHTMLに変換
    html_content = markdown.markdown(
        