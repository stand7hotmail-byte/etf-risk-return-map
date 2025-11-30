# Gemini CLI - アフィリエイト機能実装の最初の一歩（SQLAlchemy版）

## 🔍 プロジェクト状況の確認結果

あなたの調査は完全に正しいです：
- ✅ 実際のプロジェクトは **SQLAlchemy** を使用
- ✅ Peeweeの記載は誤り
- ⚠️ 既存のUserモデルが見つからない（認証機能はあるが、モデル定義の場所が不明）

---

## 📋 回答

### 質問1: Userモデルの場所について

現在のプロジェクト構造から判断すると、以下のいずれかの可能性があります：

**可能性A: Firestoreを使用（モデル不要）**
- Firebase Adminが認証とデータ保存の両方を担当
- SQLAlchemyのUserモデルが存在しない可能性

**可能性B: 認証専用（データベース保存なし）**
- JWTトークンのみで認証
- ユーザー情報はFirestoreに保存

**推奨アクション:**
```bash
# 既存のモデルを探す
find . -name "*.py" -type f | xargs grep -l "class.*Model\|Base\|Table"

# SQLAlchemyのBaseを探す
grep -r "declarative_base\|DeclarativeBase" .

# データベース初期化を探す
grep -r "create_all\|metadata.create" .
```

### 質問2: SQLAlchemyで実装する方針

**✅ はい、SQLAlchemyで進めましょう！**

理由：
1. `requirements.txt`にSQLAlchemy==2.0.43が含まれている
2. 既存のプロジェクトと一貫性が保てる
3. モダンなSQLAlchemy 2.0の機能が使える

---

## 🎯 修正版: Gemini CLIへの指示文（SQLAlchemy版）

以下をGemini CLIにコピー&ペーストしてください：

```
このFastAPIプロジェクトにアフィリエイト機能を追加するため、SQLAlchemy 2.0を使用してデータベースモデルを作成してください。

【プロジェクトコンテキスト】
- FastAPI + SQLAlchemy 2.0 を使用
- requirements.txtにSQLAlchemy==2.0.43が含まれている
- 既存の認証機能はFirebase Adminを使用
- 新しいアフィリエイト機能では通常のRDBMS（SQLite/PostgreSQL）を使用

【作成するファイル】
1. app/db/database.py（データベース設定）
2. app/models/affiliate.py（アフィリエイトモデル）

【app/db/database.py の内容】
SQLAlchemy 2.0の構文で以下を実装:
- create_engine の設定（SQLite: "sqlite:///./data/affiliate.db"）
- sessionmaker の設定
- declarative_base または DeclarativeBase
- get_db() 関数（FastAPIの依存性注入用）
- create_tables() 関数（テーブル作成用）

コード例:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import Generator

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/affiliate.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite用
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
    Base.metadata.create_all(bind=engine)
```

【app/models/affiliate.py の内容】
SQLAlchemy 2.0のMapped型アノテーションを使用して以下の2つのモデルを作成:

1. **AffiliateBroker**（証券会社情報）
   - id: Mapped[int] (primary_key=True, autoincrement=True)
   - broker_name: Mapped[str] (unique=True, index=True) 例: "interactive_brokers"
   - display_name: Mapped[str] 例: "Interactive Brokers"
   - region: Mapped[str] (index=True) 例: "US", "JP"
   - affiliate_url: Mapped[str]
   - commission_rate: Mapped[float]
   - commission_type: Mapped[str] 例: "CPA", "RevShare"
   - logo_url: Mapped[str | None] (nullable)
   - description: Mapped[str]
   - pros: Mapped[str] (JSON文字列として保存)
   - best_for: Mapped[str]
   - rating: Mapped[float]
   - is_active: Mapped[bool] (default=True)
   - created_at: Mapped[datetime] (server_default)
   - updated_at: Mapped[datetime] (server_default, onupdate)

2. **AffiliateClick**（クリック追跡）
   - id: Mapped[int] (primary_key=True)
   - broker_id: Mapped[int] (ForeignKey("affiliate_brokers.id"))
   - user_id: Mapped[str | None] (nullable)
   - session_id: Mapped[str]
   - clicked_at: Mapped[datetime] (server_default)
   - ip_address: Mapped[str | None]
   - user_agent: Mapped[str | None]
   - referrer: Mapped[str | None]
   - placement: Mapped[str] 例: "portfolio_result"
   - portfolio_data: Mapped[str | None] (JSON文字列)
   - converted: Mapped[bool] (default=False)
   - converted_at: Mapped[datetime | None] (nullable)
   
   # リレーション
   - broker: relationship("AffiliateBroker", back_populates="clicks")

コード例の開始:
```python
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.database import Base

class AffiliateBroker(Base):
    __tablename__ = "affiliate_brokers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    broker_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    # ... 続く
```

【追加要件】
- SQLAlchemy 2.0の型安全な構文（Mapped型アノテーション）を使用
- 各フィールドに適切な制約（unique, index, nullable）を設定
- created_at, updated_atには server_default=func.now() を使用
- Google形式のDocstringを追加
- 型ヒントを完全に使用
- テーブル名は複数形（affiliate_brokers, affiliate_clicks）

【参考情報】
- SQLAlchemy 2.0のMapped型システムを使用
- from typing import Optional の代わりに str | None を使用（Python 3.10+）
- datetime型にはfrom sqlalchemy.sql import funcを使用してserver_default設定

完全に動作する2つのPythonファイル（database.pyとaffiliate.py）を作成してください。
```

---

## ✅ 実行後の確認事項

### 1. ファイル構造の確認
```bash
# ディレクトリ作成（必要に応じて）
mkdir -p app/db app/models data

# 生成されたファイルの確認
ls -la app/db/database.py
ls -la app/models/affiliate.py
```

### 2. 構文チェック
```bash
# Pythonの構文チェック
python -m py_compile app/db/database.py
python -m py_compile app/models/affiliate.py
```

### 3. インポートとテーブル作成のテスト
```python
# test_db.py を作成してテスト
from app.db.database import create_tables, get_db, engine
from app.models.affiliate import AffiliateBroker, AffiliateClick
from sqlalchemy import inspect

# テーブル作成
create_tables()
print("✓ Tables created successfully")

# テーブルが作成されたか確認
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"✓ Tables in database: {tables}")

# 接続テスト
with next(get_db()) as db:
    print("✓ Database connection successful")
```

実行:
```bash
python test_db.py
```

期待される出力:
```
✓ Tables created successfully
✓ Tables in database: ['affiliate_brokers', 'affiliate_clicks']
✓ Database connection successful
```

---

## 🔄 次のステップ

このステップが完了したら、次は**初期データのシードスクリプト**を作成します。

次回Gemini CLIに渡す指示文:

```
作成したSQLAlchemyモデル（AffiliateBroker）に初期データを登録するPythonスクリプトを作成してください。

【ファイル名】
scripts/seed_brokers.py

【要件】
1. SQLAlchemy 2.0のセッション管理を使用
2. 既存データがある場合はスキップ（重複チェック）
3. トランザクション管理（エラー時はロールバック）
4. 実行結果をログ出力

【登録するデータ】（6社）

米国市場:
1. Interactive Brokers
   - broker_name: "interactive_brokers"
   - display_name: "Interactive Brokers"
   - region: "US"
   - affiliate_url: "https://ibkr.com/referral/placeholder"
   - commission_rate: 200.0
   - commission_type: "CPA"
   - description: "グローバル対応の総合証券会社。11,000以上のETFを手数料無料で取引可能。"
   - pros: '["11,000以上のETF手数料無料", "グローバル対応", "API統合可能", "プロ向けツール"]'
   - best_for: "中級〜上級投資家、自動化を希望する方"
   - rating: 4.5
   - is_active: True

2. Charles Schwab
   - broker_name: "charles_schwab"
   - display_name: "Charles Schwab"
   - region: "US"
   - commission_rate: 100.0
   - commission_type: "CPA"
   - description: "初心者に優しいUI。豊富な教育リソースと24/7サポート。"
   - pros: '["初心者向けUI", "豊富な教育リソース", "24/7サポート", "銀行機能統合"]'
   - best_for: "投資初心者"
   - rating: 4.3
   - is_active: True

3. Fidelity
   - broker_name: "fidelity"
   - display_name: "Fidelity"
   - region: "US"
   - commission_rate: 150.0
   - commission_type: "CPA"
   - description: "ゼロ手数料ETFが多数。優れたリサーチツールを提供。"
   - pros: '["ゼロ手数料ETF多数", "優れたリサーチツール", "高品質カスタマーサービス"]'
   - best_for: "長期投資家"
   - rating: 4.4
   - is_active: True

日本市場:
4. 楽天証券
   - broker_name: "rakuten_sec"
   - display_name: "楽天証券"
   - region: "JP"
   - commission_rate: 8000.0
   - commission_type: "CPA"
   - description: "楽天ポイントが貯まる・使える。米国ETFの取扱いが豊富。"
   - pros: '["楽天ポイント統合", "米国ETF豊富", "使いやすいアプリ", "投資信託100円から"]'
   - best_for: "楽天経済圏利用者、投資初心者"
   - rating: 4.6
   - is_active: True

5. SBI証券
   - broker_name: "sbi_sec"
   - display_name: "SBI証券"
   - region: "JP"
   - commission_rate: 10000.0
   - commission_type: "CPA"
   - description: "国内最大手のネット証券。商品ラインナップが最も充実。"
   - pros: '["国内最大手", "商品ラインナップ最多", "低コスト", "Tポイント・Vポイント対応"]'
   - best_for: "全ての投資家"
   - rating: 4.5
   - is_active: True

6. マネックス証券
   - broker_name: "monex_sec"
   - display_name: "マネックス証券"
   - region: "JP"
   - commission_rate: 7000.0
   - commission_type: "CPA"
   - description: "米国株・ETFの取引に強い。トレーディングツールが充実。"
   - pros: '["米国株・ETFに強い", "トレーディングツール充実", "銘柄スカウター"]'
   - best_for: "米国株投資家"
   - rating: 4.3
   - is_active: True

【コード構造】
```python
from app.db.database import SessionLocal, create_tables
from app.models.affiliate import AffiliateBroker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_brokers():
    # テーブル作成
    create_tables()
    
    db = SessionLocal()
    try:
        brokers_data = [
            # データをここに
        ]
        
        for data in brokers_data:
            # 既存チェック
            existing = db.query(AffiliateBroker).filter_by(
                broker_name=data["broker_name"]
            ).first()
            
            if existing:
                logger.info(f"⏭ Skipped: {data['display_name']} (already exists)")
                continue
            
            broker = AffiliateBroker(**data)
            db.add(broker)
            logger.info(f"✓ Added: {data['display_name']}")
        
        db.commit()
        logger.info("✓ All brokers seeded successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_brokers()
```

【実行方法】
```bash
python scripts/seed_brokers.py
```

SQLAlchemy 2.0の構文を使用し、エラーハンドリングとログ出力を含む完全なスクリプトを作成してください。
```

---

## 💡 重要な補足

### SQLAlchemy 2.0 の主な変更点

**旧バージョン（1.4以前）:**
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

**新バージョン（2.0）:**
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
```

### データベースファイルの場所

SQLiteを使用する場合:
```
data/
  └── affiliate.db  # ここに作成される
```

PostgreSQLに変更する場合:
```python
# app/db/database.py
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

---

## 🆘 トラブルシューティング

### 問題1: ModuleNotFoundError

```bash
# 解決方法: Pythonパスを設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# または
python -m scripts.seed_brokers
```

### 問題2: data/ディレクトリが存在しない

```bash
mkdir -p data
```

### 問題3: SQLAlchemy 2.0がインストールされていない

```bash
pip install "sqlalchemy>=2.0"
```

---

## 📊 成功基準

このステップが完了したと言えるのは:

1. ✅ `app/db/database.py` が作成され、動作する
2. ✅ `app/models/affiliate.py` が作成され、2つのモデルが定義されている
3. ✅ テーブルが正常に作成される
4. ✅ データベースファイル `data/affiliate.db` が生成される
5. ✅ インポートエラーがない

---

**SQLAlchemyで正しく実装を進めましょう！ご質問ありがとうございました！** 🚀