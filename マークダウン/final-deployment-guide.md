# 最終チェック & デプロイガイド

## 📊 現在の状況

### ✅ 完了
- [x] SQLインジェクション対策
- [x] 管理者認証の実装
- [x] 環境変数とシークレット管理
- [x] エラーログの漏洩防止
- [x] 入力バリデーションの強化
- [x] レート制限の個別設定

---

## 修正5: レート制限の最終実装

### 簡易版の提案

修正5は既に指示書がありますが、より**シンプルで確実な方法**を提案します。

### オプションA: 主要エンドポイントのみ厳格化（推奨）

Critical なエンドポイントにのみレート制限を追加:

```python
# app/main.py または該当する認証エンドポイント

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 登録エンドポイント - 最も厳しく
@app.post("/register")
@limiter.limit("3/minute")
async def register(request: Request, ...):
    ...

# ログインエンドポイント - 厳しめ
@app.post("/token")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...

# その他のエンドポイントはデフォルトの60/minuteのまま
```

**メリット:**
- 実装が簡単
- テストが簡単
- ブルートフォース攻撃を防げる
- 一般ユーザーには影響なし

**所要時間:** 10-15分

### オプションB: 全エンドポイントに個別設定（完璧主義）

Artifactの修正5の指示書通りに実装。

**所要時間:** 1-2時間

---

## 🎯 推奨アプローチ

**オプションAで十分です**

理由:
1. 最も危険な攻撃（ブルートフォース）を防げる
2. 実装とテストが簡単
3. 本番環境で問題が起きにくい
4. 必要なら後で拡張できる

---

## ✅ 最終チェックリスト

デプロイ前に以下を確認してください:

### セキュリティ
```bash
# 1. .env ファイルが .gitignore に含まれている
grep "^\.env$" .gitignore
# ✅ .env が出力される

# 2. .env ファイルが Git に追跡されていない
git status | grep .env
# ✅ 何も出力されない（追跡されていない）

# 3. SECRET_KEY が設定されている
grep SECRET_KEY .env
# ✅ SECRET_KEY=... が出力される

# 4. データベースファイルが .gitignore に含まれている
grep "\.db$" .gitignore
# ✅ *.db が出力される
```

### 機能

デプロイされるアプリケーションは、以下の主要な機能を備えています。これらはエンドユーザーに価値を提供し、アプリケーションの核となる体験を形成します。

- [x] **アプリケーションの起動とWebインターフェースの表示**:
  - `http://localhost:8000`へのアクセスで、アプリケーションのメインページが正しく表示されることを確認します。これにより、ユーザーはアプリケーションの利用を開始できます。

- [x] **ETF選択とポートフォリオ分析マップの生成**:
  - ユーザーが特定のETFを選択し、「Generate Map」ボタンをクリックすると、選択されたETFに基づいたポートフォリオの視覚的な分析マップが生成され、表示されることを確認します。これは、ユーザーが投資判断を下す上で重要な情報を提供します。

- [x] **個別ブローカー推薦機能**:
  - ユーザーのETF選択やポートフォリオ情報に基づき、最適な証券ブローカーが推薦されることを確認します。この機能は、ユーザーが効率的に投資を開始または最適化する手助けをします。

- [x] **ブローカー詳細ページ (`/brokers`) の表示**:
  - `/brokers`パスにアクセスした際に、利用可能な証券ブローカーの一覧、または個別のブローカーに関する詳細情報が正しく表示されることを確認します。

- [x] **アフィリエイトリンクの追跡**:
  - アプリケーション内に表示されるアフィリエイトリンク（例: ブローカー推薦からのリンク）が正しくクリックされ、そのクリックが追跡システムによって記録されることを確認します。これにより、アフィリエイト収益の発生を正確に把握できます。

- [x] **管理者ダッシュボードへの未認証アクセス制限 (`/admin/affiliate`)**:
  - 認証されていない状態で`/admin/affiliate`パスにアクセスを試みた際に、期待通り`401 Unauthorized`エラーが返されることを確認します。これは、管理者機能への不正アクセスを防止するための重要なセキュリティ対策です。

- [x] **管理者ログインとダッシュボードの表示**:
  - 適切な管理者認証情報を使用してログインに成功した後、管理者ダッシュボードが正しく表示されることを確認します。このダッシュボードから、アフィリエイトのパフォーマンスなど、アプリケーションの運用状況を監視できます。

```bash
# サーバー起動コマンド（参考）
python main.py
```
### データベース
```bash
# クリック記録が保存されている
sqlite3 data/affiliate.db "SELECT COUNT(*) FROM affiliate_clicks;"
# ✅ 数字が返る
```

---

## 🚀 デプロイ手順

### 準備

#### 1. requirements.txt の更新
```bash
pip freeze > requirements.txt
```

#### 2. .env.production の作成
```bash
cp .env.example .env.production
```

`.env.production` を編集:
```env
# 本番用の設定
DATABASE_URL=postgresql://user:password@host/database  # PostgreSQL推奨
SECRET_KEY=<本番用の強力なキー>
ENVIRONMENT=production
CORS_ORIGINS=https://your-domain.com
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# アフィリエイトURL（承認後に実際のURLに置き換え）
AFFILIATE_IBKR_URL=https://ibkr.com/referral/placeholder
# ...
```

#### 3. app.yaml の作成（Google Cloud Platform の場合）

```yaml
runtime: python39
entrypoint: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

env_variables:
  ENVIRONMENT: "production"
  RISK_FREE_RATE: "0.02"
  CACHE_TTL_SECONDS: "3600"

# Secretsは Secret Manager から読み込む
# SECRET_KEY, DATABASE_URL など

handlers:
- url: /static
  static_dir: static
  
- url: /.*
  script: auto

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

#### 4. gunicorn のインストール
```bash
pip install gunicorn
pip freeze > requirements.txt
```

---

## 📦 デプロイ方法別ガイド

### Option 1: Google Cloud Platform (App Engine)

```bash
# 1. GCP プロジェクトを設定
gcloud config set project YOUR_PROJECT_ID

# 2. Secret Manager にシークレットを保存
echo -n "your-secret-key" | gcloud secrets create SECRET_KEY --data-file=-

# 3. データベース設定（Cloud SQL推奨）
# または、SQLiteを使い続ける場合は data/ ディレクトリをアップロード

# 4. デプロイ
gcloud app deploy

# 5. URLを確認
gcloud app browse
```

**推定コスト:** 月$10-50（トラフィック次第）

### Option 2: Heroku

```bash
# 1. Herokuアプリを作成
heroku create your-app-name

# 2. PostgreSQLアドオンを追加
heroku addons:create heroku-postgresql:mini

# 3. 環境変数を設定
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set ENVIRONMENT="production"

# 4. デプロイ
git push heroku main

# 5. データベースのマイグレーション
heroku run python -c "from app.db.database import create_tables; create_tables()"
```

**推定コスト:** 月$7-25

### Option 3: Railway

```bash
# 1. Railway CLIをインストール
npm i -g @railway/cli

# 2. ログイン
railway login

# 3. プロジェクトを作成
railway init

# 4. デプロイ
railway up

# 5. 環境変数を設定
railway variables set SECRET_KEY="your-secret-key"
```

**推定コスト:** 月$5-20

### Option 4: VPS（Digital Ocean, Linode など）

```bash
# 1. サーバーにSSH接続
ssh user@your-server-ip

# 2. 必要なソフトウェアをインストール
sudo apt update
sudo apt install python3.9 python3-pip nginx

# 3. プロジェクトをクローン
git clone your-repo-url
cd your-project

# 4. 依存関係をインストール
pip3 install -r requirements.txt

# 5. .env ファイルを作成
nano .env
# 本番用の設定を記述

# 6. Supervisor で自動起動設定
sudo nano /etc/supervisor/conf.d/app.conf

# 7. Nginx でリバースプロキシ設定
sudo nano /etc/nginx/sites-available/app

# 8. 起動
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start app
```

**推定コスト:** 月$5-10

---

## 🔒 デプロイ後の確認

### 1. HTTPSが有効か確認
```bash
curl -I https://your-domain.com
# HTTP/2 200 が返ることを確認
```

### 2. APIが動作するか確認
```bash
curl https://your-domain.com/api/brokers
# JSON が返ることを確認
```

### 3. 管理者ダッシュボードの保護
```bash
curl https://your-domain.com/api/admin/affiliate/stats
# 401 Unauthorized が返ることを確認
```

### 4. Google Analytics が動作するか
```
ブラウザで開いて、GA4のリアルタイムビューでアクセスが記録されるか確認
```

---

## 📊 デプロイ後の作業

### 即座に実行
1. **Google Analytics の確認**
   - GA4でイベントが送信されているか確認

2. **アフィリエイトプログラムへの申請**
   - 楽天証券（最優先）
   - Interactive Brokers
   - 他の証券会社

3. **ドメインの設定**
   - カスタムドメインを設定（your-app.appspot.com → etf-analyzer.com）

### 数日以内
4. **Google Search Console に登録**
   ```
   https://search.google.com/search-console
   ```
   - サイトマップを送信
   - インデックス登録をリクエスト

5. **最初のブログ記事を公開**
   - 「ETF投資の始め方」
   - SEO最適化

6. **ソーシャルメディアアカウント作成**
   - Twitter / X
   - Reddit（関連サブレディット）

---

## 📈 成功指標

### 最初の1週間
- [ ] アプリケーションが安定稼働（エラーなし）
- [ ] 最低10人の訪問者
- [ ] 管理者ダッシュボードでデータが確認できる

### 最初の1ヶ月
- [ ] アフィリエイトプログラム承認
- [ ] 100人以上の訪問者
- [ ] 最低1件のアフィリエイトクリック
- [ ] ブログ記事3本公開

### 最初の3ヶ月
- [ ] 1,000人以上の訪問者
- [ ] 最初のコンバージョン（口座開設）
- [ ] $100以上の収益
- [ ] SEOランキングが向上

---

## 🆘 問題が起きたら

### よくある問題

**問題1: アプリケーションが起動しない**
```bash
# ログを確認
gcloud app logs tail -s default  # GCP
heroku logs --tail  # Heroku

# よくある原因:
# - requirements.txt に必要なパッケージがない
# - 環境変数が設定されていない
# - PORT が正しくない
```

**問題2: データベース接続エラー**
```bash
# DATABASE_URL を確認
echo $DATABASE_URL

# マイグレーションを実行
python -c "from app.db.database import create_tables; create_tables()"
```

**問題3: 静的ファイルが読み込まれない**
```
# app.yaml の handlers を確認
# nginx の設定を確認（VPSの場合）
```

---

## 🎉 デプロイ完了後

おめでとうございます！あなたのアプリケーションが本番環境で稼働しています！

### 次のステップ

1. **URLを記録**
   ```
   本番URL: https://_______________
   管理者ダッシュボード: https://_______________/admin/affiliate
   ```

2. **監視の設定**
   - Uptime monitoring（例: UptimeRobot）
   - エラー追跡（例: Sentry）

3. **バックアップの設定**
   - データベースの定期バックアップ
   - コードのGitバックアップ

4. **ドキュメントの更新**
   - README.md に本番URLを追加
   - デプロイ手順を記録

5. **チームに共有**
   - 管理者アカウント情報（安全に保管）
   - 緊急連絡先

---

## 📞 サポート

デプロイで問題が発生したら、以下の情報を教えてください:

1. **使用しているプラットフォーム**（GCP, Heroku, など）
2. **エラーメッセージ**（ログ全体）
3. **実行したコマンド**
4. **環境変数の設定**（SECRET_KEYなどは伏せ字で）

---

**修正5（レート制限）を実装してから、デプロイしますか？それともこのままデプロイしますか？**