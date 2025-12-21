# デプロイ前のセキュリティ & コード品質チェック

## 🎯 推奨アプローチ

**結論: デプロイ前にチェックすべきです**

理由:
1. 多数のコード変更がある
2. セキュリティの脆弱性がある可能性
3. 本番環境で問題が起きると修正が大変
4. アフィリエイト承認前なので、急ぐ必要がない

---

## 📋 チェックすべき項目（優先度順）

### 🔴 Critical（必須）
1. **SQLインジェクション対策**
2. **認証・認可の確認**
3. **環境変数とシークレット管理**
4. **CORS設定**
5. **エラーログの漏洩防止**

### 🟡 Important（推奨）
6. **入力バリデーション**
7. **レート制限**
8. **データベースのバックアップ**
9. **ログ管理**

### 🟢 Nice to Have（余裕があれば）
10. **コードの重複チェック**
11. **未使用コードの削除**
12. **パフォーマンス最適化**

---

## 🤖 Gemini CLI を使った自動チェック

### チェック1: SQLインジェクション対策

```
以下のプロジェクトのコードを分析し、SQLインジェクションの脆弱性がないか確認してください。

【対象ファイル】
- app/api/affiliate.py
- app/api/admin.py
- app/api/portfolio.py
- app/api/simulation.py
- app/api/analysis.py
- app/api/etf.py

【確認ポイント】
1. SQLAlchemyのORMを正しく使用しているか
2. 生のSQL文字列を使用していないか
3. ユーザー入力を直接クエリに埋め込んでいないか
4. パラメータ化されたクエリを使用しているか

【悪い例】
```python
# ❌ 危険: 生のSQL + ユーザー入力
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)
```

【良い例】
```python
# ✅ 安全: ORMを使用
user = db.query(User).filter(User.username == username).first()

# ✅ 安全: パラメータ化されたクエリ
query = text("SELECT * FROM users WHERE username = :username")
db.execute(query, {"username": username})
```

【出力形式】
1. 各ファイルの分析結果
2. 発見された問題（あれば）
3. 修正案
4. 総合評価（安全 / 要注意 / 危険）
```

---

### チェック2: 認証・認可の確認

```
以下のプロジェクトの認証・認可ロジックを分析し、セキュリティ上の問題がないか確認してください。

【対象ファイル】
- app/api/admin.py
- app/dependencies.py
- app/auth.py（存在する場合）

【確認ポイント】
1. 管理者専用エンドポイントに認証チェックがあるか
2. JWT トークンの検証が正しく行われているか
3. パスワードが平文で保存されていないか（bcrypt使用）
4. 認証なしでアクセスできる管理者機能がないか

【特に確認すべきエンドポイント】
- GET /api/admin/affiliate/stats
- GET /api/admin/affiliate/top-performing
- POST /api/admin/affiliate/conversions

【確認すべき実装】
```python
# 管理者認証が必須か？
@router.get("/admin/affiliate/stats")
async def get_stats(
    current_user: User = Depends(get_admin_user)  # ← これがあるか？
):
    ...
```

【出力形式】
1. 各エンドポイントの認証状態
2. 発見された問題（あれば）
3. 修正案
4. 総合評価
```

---

### チェック3: 環境変数とシークレット管理

```
以下のプロジェクトのシークレット管理を分析し、セキュリティリスクを確認してください。

【対象ファイル】
- app/config.py
- main.py
- .env（存在する場合）
- .gitignore

【確認ポイント】
1. APIキー、パスワード、トークンがハードコードされていないか
2. .env ファイルが .gitignore に含まれているか
3. Firebase のAPIキーが公開されていないか（これは許容される場合もある）
4. データベースURLが環境変数から読み込まれているか

【ハードコードされていないか確認すべき情報】
- データベース接続文字列
- Firebase API Key（クライアント側は許容）
- Firebase Service Account（サーバー側は絶対NG）
- Google Cloud プロジェクトID
- アフィリエイトURL（これは環境変数化推奨）

【チェックすべきファイル内容】
```python
# ❌ 危険: ハードコード
DATABASE_URL = "postgresql://user:password@localhost/db"

# ✅ 安全: 環境変数から読み込み
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
```

【.gitignore に含まれるべきもの】
- .env
- *.db
- __pycache__/
- *.pyc
- .venv/
- venv/

【出力形式】
1. ハードコードされたシークレットのリスト
2. .gitignore の評価
3. 修正案
4. 総合評価
```

---

### チェック4: CORS設定の確認

```
以下のプロジェクトのCORS設定を確認し、本番環境で問題がないか分析してください。

【対象ファイル】
- app/main.py
- main.py（ルート）

【確認ポイント】
1. CORS設定が存在するか
2. allow_origins に "*"（全て許可）が設定されていないか
3. 本番環境のドメインのみを許可する設定になっているか
4. credentials（認証情報）の扱いが適切か

【現在の設定を確認】
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ← これが危険
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

【推奨される本番環境設定】
```python
import os

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 環境変数から読み込み
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

【出力形式】
1. 現在のCORS設定
2. セキュリティリスク評価
3. 修正案
4. 環境別の推奨設定
```

---

### チェック5: エラーログの漏洩防止

```
以下のプロジェクトのエラーハンドリングを確認し、機密情報がログに漏れていないか分析してください。

【対象ファイル】
- app/api/ 配下の全ファイル
- app/main.py

【確認ポイント】
1. エラー時にスタックトレースが完全に返されていないか
2. データベース接続エラーがそのまま表示されていないか
3. 機密情報（トークン、パスワード）がログに出力されていないか
4. 本番環境用のエラーハンドラーが設定されているか

【危険な例】
```python
# ❌ スタックトレース全部返す
except Exception as e:
    return {"error": str(e)}  # データベース構造などが漏れる可能性

# ❌ 機密情報をログ出力
logger.info(f"User login: {username}, password: {password}")
```

【安全な例】
```python
# ✅ 一般的なエラーメッセージ
except Exception as e:
    logger.error(f"Database error: {e}")  # サーバーログには詳細
    return {"error": "An error occurred"}  # ユーザーには一般的なメッセージ

# ✅ 機密情報は出力しない
logger.info(f"User login attempt: {username}")  # パスワードは出力しない
```

【出力形式】
1. 発見された問題箇所
2. リスク評価
3. 修正案
4. 推奨されるエラーハンドリング戦略
```

---

### チェック6: 入力バリデーション

```
以下のプロジェクトの入力バリデーションを確認し、不正な入力に対する防御が適切か分析してください。

【対象ファイル】
- app/schemas.py
- app/api/ 配下の全ファイル

【確認ポイント】
1. Pydanticスキーマで全ての入力が検証されているか
2. 文字列長の制限があるか
3. 数値の範囲チェックがあるか
4. メールアドレスや日付のフォーマット検証があるか
5. ファイルアップロードがある場合、サイズとタイプの検証があるか

【確認すべきスキーマ】
```python
class BrokerTrackingRequest(BaseModel):
    broker_id: int  # 正の整数チェックは？
    placement: str  # 文字列長は？許可された値のみ？
    portfolio_data: dict | None  # dictの構造は検証されている？
```

【推奨される改善】
```python
from pydantic import Field, validator

class BrokerTrackingRequest(BaseModel):
    broker_id: int = Field(gt=0, description="Broker ID must be positive")
    placement: str = Field(
        max_length=50,
        regex="^[a-z_]+$",  # 英小文字とアンダースコアのみ
        description="Placement location"
    )
    portfolio_data: dict | None = None
    
    @validator('placement')
    def validate_placement(cls, v):
        allowed = ['portfolio_result', 'broker_page', 'blog_post']
        if v not in allowed:
            raise ValueError(f'Placement must be one of {allowed}')
        return v
```

【出力形式】
1. 各スキーマの検証状態
2. 不足している検証
3. 修正案
4. 総合評価
```

---

### チェック7: レート制限の確認

```
以下のプロジェクトのレート制限を確認し、DoS攻撃への対策が適切か分析してください。

【対象ファイル】
- app/main.py
- app/api/ 配下の全エンドポイント

【確認ポイント】
1. slowapi または類似のライブラリが使用されているか
2. レート制限が設定されているか
3. 重要なエンドポイント（認証、登録）に厳しい制限があるか
4. APIキーなしでアクセスできるエンドポイントに制限があるか

【現在の設定を確認】
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/register")
@limiter.limit("5/minute")  # ← 設定されているか？
async def register(...):
    ...
```

【推奨されるレート制限】
- 認証エンドポイント: 5回/分
- 登録エンドポイント: 3回/分
- 一般的なGETエンドポイント: 60回/分
- POSTエンドポイント: 30回/分
- 管理者エンドポイント: 100回/分（認証済みのため緩め）

【出力形式】
1. 現在のレート制限設定
2. 不足しているエンドポイント
3. 推奨される設定
4. 実装コード例
```

---

## 🔧 実行方法

### ステップ1: ファイルのコピー

Gemini CLIで分析するために、主要ファイルの内容を準備:

```bash
# 一時ディレクトリに主要ファイルをコピー
mkdir -p /tmp/security-check
cp app/api/*.py /tmp/security-check/
cp app/config.py /tmp/security-check/
cp app/schemas.py /tmp/security-check/
cp app/main.py /tmp/security-check/
cp .gitignore /tmp/security-check/
```

### ステップ2: Gemini CLIで分析

各チェック項目を順番に実行:

```bash
# チェック1: SQLインジェクション
gemini "$(cat チェック1の指示文) 
対象: /tmp/security-check/affiliate.py の内容: $(cat /tmp/security-check/affiliate.py)"

# チェック2: 認証・認可
gemini "$(cat チェック2の指示文)
対象: /tmp/security-check/admin.py の内容: $(cat /tmp/security-check/admin.py)"

# ... 以下同様
```

### ステップ3: 結果の記録

各チェックの結果を記録:

```markdown
# セキュリティチェック結果

## チェック1: SQLインジェクション対策
- 状態: ✅ 安全 / ⚠️ 要注意 / ❌ 危険
- 問題: [発見された問題を記載]
- 修正: [必要な修正を記載]

## チェック2: 認証・認可
- 状態: ✅ 安全 / ⚠️ 要注意 / ❌ 危険
- 問題: [発見された問題を記載]
- 修正: [必要な修正を記載]

...
```

---

## 🚀 問題がなければデプロイ

すべてのチェックで ✅ または ⚠️（軽微な問題のみ）なら:

### デプロイ前の最終準備

```bash
# 1. 依存関係を最新に
pip freeze > requirements.txt

# 2. .gitignore を確認
cat .gitignore
# .env, *.db が含まれているか確認

# 3. 環境変数の準備
cp .env.example .env.production
# 本番用の値を設定

# 4. データベースのバックアップ
cp data/affiliate.db data/affiliate.db.backup
```

### デプロイ

```bash
# Google Cloud Platform の場合
gcloud app deploy

# または他のプラットフォーム
# Heroku: git push heroku main
# AWS: eb deploy
```

---

## ⏰ 推奨スケジュール

### 今日〜明日
- [ ] チェック1-3（Critical）を実行
- [ ] 発見された問題を修正

### 2-3日以内
- [ ] チェック4-5（Critical）を実行
- [ ] 修正

### 1週間以内
- [ ] チェック6-7（Important）を実行
- [ ] 修正
- [ ] すべて問題なければデプロイ

### デプロイ後
- [ ] アフィリエイトプログラムに申請（承認には数日〜数週間）
- [ ] ブログ記事を書き始める
- [ ] SEO対策

---

## 💡 重要なポイント

### デプロイを急ぐ必要がない理由

1. **アフィリエイト承認待ち**
   - どの証券会社も審査に3-30日かかる
   - その間にコードを改善できる

2. **初期トラフィックは少ない**
   - SEO効果が出るまで数週間〜数ヶ月
   - バグ修正の時間は十分ある

3. **本番環境でのバグは高コスト**
   - セキュリティ問題が発覚すると信頼を失う
   - 修正とデプロイに時間がかかる

### チェックをスキップしてデプロイする場合のリスク

❌ SQLインジェクション → データベース全体が漏洩
❌ 認証不備 → 他人のデータが見られる
❌ CORS設定ミス → XSS攻撃の可能性
❌ エラー情報漏洩 → システム構造がバレる

---

## 📞 次のステップ

1. **まず Critical（チェック1-5）を Gemini CLI で実行**
2. **問題があれば修正**
3. **問題なければ、または軽微な問題のみなら、デプロイを検討**

セキュリティチェックの結果を教えてください。問題があれば一緒に修正しましょう！