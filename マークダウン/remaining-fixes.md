# 残りのセキュリティ修正（Important）

## 🟡 修正が必要な項目

4. ~~CORS設定~~ → 既に安全（改善の余地ありだが許容範囲）
5. **入力バリデーション** ⚠️ 修正推奨
6. **レート制限** ⚠️ 修正推奨

---

## 修正4: 入力バリデーションの強化

### 問題
- パスワードの最小長・複雑性チェックがない
- `broker_id` の範囲チェックがない
- `placement` の許可値チェックがない
- `portfolio_data` の内部構造が未検証

### Gemini CLIへの指示文

```
以下の要件に従って、app/schemas.py の入力バリデーションを強化してください。

【現在の問題】
- Pydanticスキーマで詳細なバリデーションが不足
- 不正な値がデータベースに保存される可能性
- 予期せぬエラーのリスク

【要求される修正】

1. UserCreate スキーマの強化

```python
from pydantic import BaseModel, Field, validator
import re

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """ユーザー名は英数字とアンダースコアのみ"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """パスワードの複雑性チェック"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

2. BrokerTrackingRequest スキーマの強化

```python
class BrokerTrackingRequest(BaseModel):
    broker_id: int = Field(
        gt=0,
        description="Broker ID must be a positive integer"
    )
    placement: str = Field(
        max_length=50,
        description="Placement location"
    )
    portfolio_data: dict | None = Field(
        default=None,
        description="Portfolio data (optional)"
    )
    
    @validator('placement')
    def validate_placement(cls, v):
        """配置場所は許可された値のみ"""
        allowed_placements = [
            'portfolio_result',
            'broker_page',
            'blog_post',
            'comparison_page'
        ]
        if v not in allowed_placements:
            raise ValueError(f'Placement must be one of: {", ".join(allowed_placements)}')
        return v
    
    @validator('portfolio_data')
    def validate_portfolio_data(cls, v):
        """ポートフォリオデータの構造検証"""
        if v is None:
            return v
        
        # tickers と weights が含まれているか確認
        if 'tickers' in v:
            if not isinstance(v['tickers'], list):
                raise ValueError('portfolio_data.tickers must be a list')
            if not all(isinstance(t, str) for t in v['tickers']):
                raise ValueError('portfolio_data.tickers must contain only strings')
        
        if 'weights' in v:
            if not isinstance(v['weights'], dict):
                raise ValueError('portfolio_data.weights must be a dict')
        
        return v
```

3. AffiliateBrokerBase スキーマの修正

```python
class AffiliateBrokerBase(BaseModel):
    broker_name: str = Field(
        min_length=1,
        max_length=100,
        description="Unique broker identifier"
    )
    display_name: str = Field(
        min_length=1,
        max_length=200,
        description="Display name"
    )
    region: str = Field(
        max_length=10,
        description="Region code"
    )
    affiliate_url: str = Field(
        max_length=500,
        description="Affiliate URL"
    )
    commission_rate: float = Field(
        ge=0,
        description="Commission rate (must be non-negative)"
    )
    commission_type: str = Field(
        max_length=20,
        description="Commission type"
    )
    description: str = Field(
        max_length=1000,
        description="Broker description"
    )
    pros: str = Field(
        description="JSON string of pros"
    )  # JSON文字列として保存されている場合
    best_for: str = Field(
        max_length=200,
        description="Best for target audience"
    )
    rating: float = Field(
        ge=0,
        le=5,
        description="Rating from 0 to 5"
    )
    
    @validator('region')
    def validate_region(cls, v):
        """地域コードは許可された値のみ"""
        allowed_regions = ['US', 'JP', 'EU', 'Global', 'Global ex-US']
        if v not in allowed_regions:
            raise ValueError(f'Region must be one of: {", ".join(allowed_regions)}')
        return v
    
    @validator('commission_type')
    def validate_commission_type(cls, v):
        """報酬タイプは許可された値のみ"""
        allowed_types = ['CPA', 'RevShare', 'Hybrid']
        if v not in allowed_types:
            raise ValueError(f'Commission type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('pros')
    def validate_pros(cls, v):
        """prosがJSON形式の文字列か確認"""
        import json
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError('pros must be a JSON array')
            if not all(isinstance(item, str) for item in parsed):
                raise ValueError('pros must contain only strings')
        except json.JSONDecodeError:
            raise ValueError('pros must be valid JSON')
        return v
```

4. その他のスキーマも同様に強化

- CustomPortfolioRequest
- OptimizeByReturnRequest
- OptimizeByRiskRequest
- MonteCarloRequest
など

【追加要件】
- 既存のコードスタイルに合わせる
- 型ヒントを使用（Python 3.10+ の | 記法を使用）
- エラーメッセージは英語で分かりやすく
- Docstringを追加

【出力】
完全に動作する app/schemas.py ファイルを生成してください。
既存のスキーマをすべて含み、上記のバリデーションを追加してください。
```

---

## 修正5: レート制限の個別設定

### 問題
- すべてのエンドポイントに一律の制限
- 認証・登録エンドポイントに厳しい制限がない
- ブルートフォース攻撃のリスク

### Gemini CLIへの指示文

```
以下の要件に従って、エンドポイント別のレート制限を設定してください。

【現在の問題】
- すべてのエンドポイントに一律のデフォルトレート制限
- 高リスクなエンドポイントに対する保護が不足

【要求される実装】

1. app/main.py の修正

slowapi の設定を強化:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Limiter インスタンスを作成
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"]  # デフォルト: 1分間に60リクエスト
)

app = FastAPI(...)

# Limiter をアプリケーションに設定
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
```

2. 認証エンドポイントに厳しい制限

```python
# 既存の認証エンドポイント（例: app/api/auth.py または main.py）

@app.post("/register")
@limiter.limit("3/minute")  # 1分間に3回まで
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # 既存のロジック
    ...

@app.post("/token")
@limiter.limit("5/minute")  # 1分間に5回まで
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 既存のロジック
    ...

@app.post("/token/google")
@limiter.limit("10/minute")  # Google OAuth: 1分間に10回
async def login_google(
    request: Request,
    token_data: dict
):
    # 既存のロジック
    ...
```

3. 一般的なエンドポイントの制限

```python
# app/api/affiliate.py

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@router.get("/brokers")
@limiter.limit("60/minute")  # GET: 1分間に60回
async def get_brokers(request: Request, ...):
    ...

@router.post("/brokers/track-click")
@limiter.limit("30/minute")  # POST: 1分間に30回
async def track_click(request: Request, ...):
    ...
```

4. 管理者エンドポイントの制限

```python
# app/api/admin.py

@router.get("/affiliate/stats")
@limiter.limit("100/minute")  # 管理者: 1分間に100回（認証済みのため緩め）
async def get_stats(
    request: Request,
    current_user: dict = Depends(get_admin_user),
    ...
):
    ...
```

5. 重いエンドポイントの制限

```python
# app/api/simulation.py

@router.post("/monte_carlo")
@limiter.limit("10/minute")  # 計算が重い: 1分間に10回
async def monte_carlo(request: Request, ...):
    ...

@router.post("/historical_dca")
@limiter.limit("20/minute")  # 中程度: 1分間に20回
async def historical_dca(request: Request, ...):
    ...
```

【推奨されるレート制限設定】

| エンドポイント | レート制限 | 理由 |
|---------------|-----------|------|
| POST /register | 3/minute | アカウント作成の乱用防止 |
| POST /token | 5/minute | ブルートフォース攻撃防止 |
| POST /token/google | 10/minute | OAuth悪用防止 |
| GET /api/brokers | 60/minute | 一般的な読み取り |
| POST /api/brokers/track-click | 30/minute | クリック追跡 |
| GET /api/admin/* | 100/minute | 管理者（認証済み） |
| POST /simulation/monte_carlo | 10/minute | CPU負荷が高い |
| POST /portfolio/* | 30/minute | 計算処理 |

【追加要件】
- 既存のコードに統合
- limiter インスタンスを適切に共有
- エラーメッセージをカスタマイズ（オプション）
- 型ヒントを使用

【カスタムエラーメッセージ（オプション）】

```python
from fastapi.responses import JSONResponse

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail
        }
    )
```

【出力】
1. 修正された app/main.py（limiter設定部分）
2. 各APIファイルの修正例（affiliate.py, admin.py, など）
3. レート制限の一覧表
```

---

## ✅ 修正完了後のテスト

### テスト1: 入力バリデーション

```bash
# パスワードが弱い場合
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "weak"}'

# 期待される応答: 422 Unprocessable Entity
# "Password must contain at least one uppercase letter"
```

```bash
# broker_id が負の値
curl -X POST http://localhost:8000/api/brokers/track-click \
  -H "Content-Type: application/json" \
  -d '{"broker_id": -1, "placement": "test"}'

# 期待される応答: 422 Unprocessable Entity
# "Broker ID must be a positive integer"
```

```bash
# placement が不正な値
curl -X POST http://localhost:8000/api/brokers/track-click \
  -H "Content-Type: application/json" \
  -d '{"broker_id": 1, "placement": "invalid_place"}'

# 期待される応答: 422 Unprocessable Entity
# "Placement must be one of: portfolio_result, broker_page, ..."
```

### テスト2: レート制限

```bash
# レート制限のテスト（5回ログイン試行）
for i in {1..6}; do
  echo "Attempt $i:"
  curl -X POST http://localhost:8000/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test&password=test"
  echo ""
done

# 6回目は 429 Too Many Requests が返るはず
```

```bash
# 管理者エンドポイントのレート制限テスト
for i in {1..101}; do
  curl -s http://localhost:8000/api/admin/affiliate/stats \
    -H "Authorization: Bearer YOUR_TOKEN" > /dev/null
done

# 101回目は 429 が返るはず
```

---

## 📊 修正前後の比較

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| パスワード | ❌ 任意の文字列 | ✅ 8文字以上、大小英数字必須 |
| broker_id | ❌ 負の値も可 | ✅ 正の整数のみ |
| placement | ❌ 任意の文字列 | ✅ 許可された値のみ |
| ログイン試行 | ❌ 無制限 | ✅ 5回/分 |
| 登録試行 | ❌ 無制限 | ✅ 3回/分 |
| 重い処理 | ❌ 無制限 | ✅ 10回/分 |

---

## 🚀 すべて完了したら

### 最終チェックリスト

```markdown
## Critical問題
- [x] 管理者認証の実装
- [x] 環境変数とシークレット管理
- [x] エラーログの漏洩防止

## Important問題
- [ ] 入力バリデーションの強化
- [ ] レート制限の個別設定

## 最終確認
- [ ] すべての機能が正常に動作する
- [ ] テストが通る
- [ ] .env ファイルが .gitignore に含まれている
- [ ] SECRET_KEY が設定されている
- [ ] 本番環境用の設定が準備されている
```

### デプロイの準備

すべて ✅ になったら:

```bash
# 1. requirements.txt を更新
pip freeze > requirements.txt

# 2. .env.production を作成
cp .env.example .env.production
# 本番用の値を設定

# 3. app.yaml を確認（GCP App Engine の場合）
cat app.yaml

# 4. デプロイ
gcloud app deploy
```

---

## 📝 次のステップ

1. **修正4（入力バリデーション）を実行**
   - Gemini CLIで指示文を実行
   - 生成された schemas.py を確認
   - テスト

2. **修正5（レート制限）を実行**
   - Gemini CLIで指示文を実行
   - 各APIファイルを更新
   - テスト

3. **最終確認**
   - 全機能のテスト
   - セキュリティチェックリスト確認

4. **デプロイ！**

---

**修正4と修正5、どちらから始めますか？それとも、Critical問題の修正内容を確認したいですか？**