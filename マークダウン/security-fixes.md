# セキュリティ修正 - Critical問題の解決

## 🔴 修正が必須の問題（優先度順）

1. **管理者認証の欠如** ❌ 最優先
2. **環境変数とシークレット管理** ❌ 最優先
3. **エラーログの漏洩** ❌ 最優先

---

## 修正1: 管理者認証の実装

### 問題
- `get_admin_user` 関数がプレースホルダー
- 管理者ダッシュボードに誰でもアクセス可能
- JWT認証が機能していない

### Gemini CLIへの指示文

```
以下の要件に従って、管理者認証機能を実装してください。

【現在の状況】
- app/dependencies.py に get_admin_user 関数が存在するが、プレースホルダー
- JWT認証の仕組みは既に存在（ユーザー認証用）
- 管理者エンドポイントは app/api/admin.py に存在

【要求される実装】

1. app/dependencies.py の修正

既存のJWT認証ロジックを拡張し、以下の関数を実装:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """
    JWTトークンから現在のユーザーを取得
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "is_admin": payload.get("is_admin", False)}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    管理者権限を確認
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

2. ユーザー登録時に管理者フラグを追加

既存のユーザー登録ロジック（おそらく別ファイル）に以下を追加:

```python
# 最初のユーザーを自動的に管理者にする
# または、特定のユーザー名を管理者にする

def create_user(username: str, password: str, db):
    # 既存のロジック...
    
    # 最初のユーザーを管理者にする
    user_count = db.query(User).count()
    is_admin = (user_count == 0)
    
    # または、特定のユーザー名を管理者にする
    # is_admin = (username == "admin")
    
    # ユーザー作成...
    return user
```

3. JWT トークン生成時に is_admin を含める

```python
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    # is_admin フラグを含める
    to_encode.update({"is_admin": data.get("is_admin", False)})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

4. app/api/admin.py の確認

すべての管理者エンドポイントで get_admin_user を使用していることを確認:

```python
@router.get("/affiliate/stats")
async def get_affiliate_stats(
    current_user: dict = Depends(get_admin_user),  # ← これが必須
    start_date: str = None,
    end_date: str = None
):
    # 既存のロジック
    ...
```

【追加要件】
- 既存のコードスタイルに合わせる
- 型ヒントを使用
- エラーメッセージは英語
- Docstringを追加（Google形式）

【出力】
完全に動作する app/dependencies.py ファイルを生成してください。
```

---

## 修正2: 環境変数とシークレット管理

### 問題
- `.gitignore` に `.env` が含まれていない
- `app/database.py` でデータベースURLがハードコード
- シークレットが漏洩するリスク

### Gemini CLIへの指示文

```
以下の要件に従って、環境変数とシークレット管理を適切に実装してください。

【修正が必要なファイル】
1. .gitignore
2. app/db/database.py
3. .env.example（新規作成）

【修正1: .gitignore の更新】

既存の .gitignore に以下を追加（重複がないか確認）:

```
# 環境変数
.env
.env.local
.env.production

# データベース
*.db
*.sqlite
*.sqlite3
data/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# ログ
*.log
logs/

# 一時ファイル
*.tmp
*.bak
```

【修正2: app/db/database.py の更新】

現在のハードコードされた部分を環境変数から読み込むように変更:

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

# 環境変数からデータベースURLを取得
# デフォルトはSQLite（開発環境用）
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/affiliate.db"
)

# SQLiteの場合のみcheck_same_threadを無効化
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """全てのテーブルを作成"""
    Base.metadata.create_all(bind=engine)
```

【修正3: .env.example の作成】

プロジェクトルートに .env.example を作成（実際の値は含めない）:

```env
# データベース
DATABASE_URL=sqlite:///./data/affiliate.db

# JWT認証
SECRET_KEY=your-secret-key-change-in-production-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# アプリケーション設定
RISK_FREE_RATE=0.02
CACHE_TTL_SECONDS=3600

# CORS設定（カンマ区切り）
CORS_ORIGINS=http://localhost:8000,http://localhost:3000

# Google Analytics
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# アフィリエイトURL（承認後に実際のURLに置き換え）
AFFILIATE_IBKR_URL=https://ibkr.com/referral/placeholder
AFFILIATE_SCHWAB_URL=https://www.schwab.com/referral/placeholder
AFFILIATE_FIDELITY_URL=https://www.fidelity.com/referral/placeholder
AFFILIATE_RAKUTEN_URL=https://www.rakuten-sec.co.jp/placeholder
AFFILIATE_SBI_URL=https://www.sbisec.co.jp/placeholder
AFFILIATE_MONEX_URL=https://info.monex.co.jp/placeholder

# 本番環境用（Google Cloud Platform）
# PROJECT_ID=your-gcp-project-id
```

【修正4: README.md に環境変数の説明を追加】

README.md のセットアップセクションに以下を追加:

```markdown
### 環境変数の設定

1. `.env.example` をコピーして `.env` を作成:
   ```bash
   cp .env.example .env
   ```

2. `.env` ファイルを編集して実際の値を設定:
   ```bash
   nano .env
   ```

3. **重要**: `.env` ファイルは絶対にGitにコミットしないでください。

#### 必須の環境変数

- `SECRET_KEY`: JWT署名用のシークレットキー（最低32文字のランダムな文字列）
  ```bash
  # 生成方法
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- `DATABASE_URL`: データベース接続URL
  - 開発環境: `sqlite:///./data/affiliate.db`
  - 本番環境: PostgreSQL等の接続文字列
```

【追加要件】
- 既存のファイル構造を維持
- コメントは日本語でも可
- セキュリティのベストプラクティスに従う

【出力】
1. 更新された .gitignore
2. 更新された app/db/database.py
3. 新しい .env.example
4. README.md への追記内容
```

---

## 修正3: エラーログの漏洩防止

### 問題
- エラーの詳細がそのまま返される
- スタックトレースが外部に漏洩
- try-catch ブロックが不足

### Gemini CLIへの指示文

```
以下の要件に従って、エラーハンドリングを改善してください。

【現在の問題】
- app/main.py の ValueError ハンドラーがエラー詳細をそのまま返す
- 各APIエンドポイントで予期せぬ例外に対する処理が不足
- 内部情報が外部に漏洩するリスク

【要求される実装】

1. app/main.py にグローバルエラーハンドラーを追加

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback
import os

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(...)

# 環境判定（本番環境ではデバッグ情報を隠す）
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全ての予期せぬ例外をキャッチ
    """
    # サーバーログには詳細を記録
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # ユーザーには一般的なメッセージのみ
    if IS_PRODUCTION:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred. Please try again later."
            }
        )
    else:
        # 開発環境ではデバッグ情報を含める
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """
    ValueErrorの処理
    """
    logger.warning(f"ValueError: {exc} at {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Invalid input data"  # 詳細は出さない
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Pydanticのバリデーションエラー
    """
    logger.warning(f"Validation error: {exc.errors()} at {request.url.path}")
    
    # バリデーションエラーは具体的に返す（ユーザーが修正できるように）
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )
```

2. 各APIエンドポイントに try-catch を追加

app/api/affiliate.py などの例:

```python
@router.post("/brokers/track-click")
async def track_click(
    data: BrokerTrackingRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # 既存のロジック
        click = AffiliateClick(
            broker_id=data.broker_id,
            placement=data.placement,
            # ...
        )
        db.add(click)
        db.commit()
        db.refresh(click)
        
        logger.info(f"Click tracked: {click.click_id}")
        
        return {
            "success": True,
            "click_id": click.click_id,
            "redirect_url": broker.affiliate_url
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database error in track_click: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record click"  # 詳細は出さない
        )
    except Exception as e:
        logger.error(f"Unexpected error in track_click: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred"
        )
```

3. ロギングのベストプラクティス

```python
import logging

logger = logging.getLogger(__name__)

# ✅ 良い例: 機密情報を含めない
logger.info(f"User login attempt: {username}")
logger.error(f"Database connection failed: {db_host}")

# ❌ 悪い例: 機密情報を出力
logger.info(f"User login: {username}, password: {password}")  # NG
logger.error(f"Database error: {connection_string}")  # NG
```

【修正が必要なファイル】
- app/main.py（グローバルエラーハンドラー）
- app/api/affiliate.py
- app/api/admin.py
- app/api/portfolio.py
- その他の API ファイル

【追加要件】
- 既存のコードスタイルに合わせる
- ログレベルを適切に使い分ける（INFO, WARNING, ERROR）
- 型ヒントを使用
- Docstringを追加

【出力】
各ファイルの修正版を生成してください。特に:
1. app/main.py の完全版
2. app/api/affiliate.py の修正例（他のファイルも同様に適用）
```

---

## 🔄 修正の実行順序

### ステップ1: 環境変数とシークレット管理（最優先）
```bash
# 理由: 他の修正で SECRET_KEY などが必要になるため
```

1. Gemini CLIで「修正2」を実行
2. 生成されたファイルを保存:
   - `.gitignore`
   - `app/db/database.py`
   - `.env.example`
3. `.env` ファイルを作成:
   ```bash
   cp .env.example .env
   # SECRET_KEY を生成
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   # 生成された値を .env に設定
   ```

### ステップ2: 管理者認証の実装
```bash
# 理由: 環境変数が設定されていることが前提
```

1. Gemini CLIで「修正1」を実行
2. 生成された `app/dependencies.py` を保存
3. テスト:
   ```bash
   # 管理者ユーザーを作成
   # 管理者ダッシュボードにアクセスして401が返ることを確認
   ```

### ステップ3: エラーログの漏洩防止
```bash
# 理由: エラーハンドリングは最後に統合
```

1. Gemini CLIで「修正3」を実行
2. 生成されたファイルを保存
3. テスト:
   ```bash
   # わざとエラーを起こして、一般的なメッセージが返ることを確認
   ```

---

## ✅ 修正完了後の確認

### 1. .env ファイルの確認
```bash
# .env が存在する
ls -la .env

# .gitignore に含まれている
grep ".env" .gitignore
```

### 2. 管理者認証のテスト
```bash
# トークンなしでアクセス → 401
curl http://localhost:8000/api/admin/affiliate/stats

# 一般ユーザーでアクセス → 403
# 管理者ユーザーでアクセス → 200
```

### 3. エラーハンドリングのテスト
```bash
# 存在しないブローカーIDでクリック追跡 → 一般的なエラーメッセージ
curl -X POST http://localhost:8000/api/brokers/track-click \
  -H "Content-Type: application/json" \
  -d '{"broker_id": 999, "placement": "test"}'

# スタックトレースが返らないことを確認
```

---

## 📊 修正前後の比較

| 項目 | 修正前 | 修正後 |
|------|--------|--------|
| 管理者認証 | ❌ 誰でもアクセス可能 | ✅ JWT + is_admin チェック |
| シークレット管理 | ❌ ハードコード | ✅ 環境変数 |
| エラー情報 | ❌ 詳細が漏洩 | ✅ 一般的なメッセージ |
| .gitignore | ❌ .env が含まれない | ✅ 追加済み |

---

## 🚀 次のステップ

Critical問題を修正したら:

1. **⚠️ 要注意問題の修正**
   - 入力バリデーション（チェック6）
   - レート制限（チェック7）

2. **再テスト**
   - すべての機能が正常に動作するか確認

3. **デプロイ**
   - Google Cloud Platform または他のプラットフォーム

---

**まず「修正2（環境変数）」から始めましょう！Gemini CLIで実行して、結果を教えてください。**