# -*- coding: utf-8 -*-
"""
Script to seed initial affiliate broker data into the database.
"""
import json
import logging
import os
from datetime import datetime

from app.db.database import SessionLocal, create_tables
from app.models.affiliate import AffiliateBroker

# Ensure the 'data' directory exists for the SQLite database
os.makedirs("data", exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def seed_brokers():
    """
    Seeds initial affiliate broker data into the database.
    Skips brokers that already exist based on broker_name.
    """
    logger.info("Starting broker seeding process...")

    # Ensure tables are created before seeding
    try:
        create_tables()
        logger.info("Database tables ensured to be created.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return

    db = SessionLocal()
    try:
        brokers_data = [
            # US Market
            {
                "broker_name": "interactive_brokers",
                "display_name": "Interactive Brokers",
                "region": "US",
                "affiliate_url": "https://ibkr.com/referral/placeholder",
                "commission_rate": 200.0,
                "commission_type": "CPA",
                "description": "グローバル対応の総合証券会社。11,000以上のETFを手数料無料で取引可能。",
                "pros": json.dumps(["11,000以上のETF手数料無料", "グローバル対応", "API統合可能", "プロ向けツール"]),
                "best_for": "中級〜上級投資家、自動化を希望する方",
                "rating": 4.5,
                "is_active": True,
            },
            {
                "broker_name": "charles_schwab",
                "display_name": "Charles Schwab",
                "region": "US",
                "affiliate_url": "https://www.schwab.com/referral/placeholder", # Placeholder
                "commission_rate": 100.0,
                "commission_type": "CPA",
                "description": "初心者に優しいUI。豊富な教育リソースと24/7サポート。",
                "pros": json.dumps(["初心者向けUI", "豊富な教育リソース", "24/7サポート", "銀行機能統合"]),
                "best_for": "投資初心者",
                "rating": 4.3,
                "is_active": True,
            },
            {
                "broker_name": "fidelity",
                "display_name": "Fidelity",
                "region": "US",
                "affiliate_url": "https://www.fidelity.com/referral/placeholder", # Placeholder
                "commission_rate": 150.0,
                "commission_type": "CPA",
                "description": "ゼロ手数料ETFが多数。優れたリサーチツールを提供。",
                "pros": json.dumps(["ゼロ手数料ETF多数", "優れたリサーチツール", "高品質カスタマーサービス"]),
                "best_for": "長期投資家",
                "rating": 4.4,
                "is_active": True,
            },
            # JP Market
            {
                "broker_name": "rakuten_sec",
                "display_name": "楽天証券",
                "region": "JP",
                "affiliate_url": "https://www.rakuten-sec.co.jp/referral/placeholder", # Placeholder
                "commission_rate": 8000.0,
                "commission_type": "CPA",
                "description": "楽天ポイントが貯まる・使える。米国ETFの取扱いが豊富。",
                "pros": json.dumps(["楽天ポイント統合", "米国ETF豊富", "使いやすいアプリ", "投資信託100円から"]),
                "best_for": "楽天経済圏利用者、投資初心者",
                "rating": 4.6,
                "is_active": True,
            },
            {
                "broker_name": "sbi_sec",
                "display_name": "SBI証券",
                "region": "JP",
                "affiliate_url": "https://www.sbisec.co.jp/referral/placeholder", # Placeholder
                "commission_rate": 10000.0,
                "commission_type": "CPA",
                "description": "国内最大手のネット証券。商品ラインナップが最も充実。",
                "pros": json.dumps(["国内最大手", "商品ラインナップ最多", "低コスト", "Tポイント・Vポイント対応"]),
                "best_for": "全ての投資家",
                "rating": 4.5,
                "is_active": True,
            },
            {
                "broker_name": "monex_sec",
                "display_name": "マネックス証券",
                "region": "JP",
                "affiliate_url": "https://www.monex.co.jp/referral/placeholder", # Placeholder
                "commission_rate": 7000.0,
                "commission_type": "CPA",
                "description": "米国株・ETFの取引に強い。トレーディングツールが充実。",
                "pros": json.dumps(["米国株・ETFに強い", "トレーディングツール充実", "銘柄スカウター"]),
                "best_for": "米国株投資家",
                "rating": 4.3,
                "is_active": True,
            },
        ]

        for data in brokers_data:
            existing = db.query(AffiliateBroker).filter_by(
                broker_name=data["broker_name"]
            ).first()

            if existing:
                logger.info(f"⏭ Skipped: {data['display_name']} (already exists)")
            else:
                broker = AffiliateBroker(**data)
                db.add(broker)
                logger.info(f"✓ Added: {data['display_name']}")

        db.commit()
        logger.info("✓ All brokers seeded successfully.")

    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during seeding process: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_brokers()
