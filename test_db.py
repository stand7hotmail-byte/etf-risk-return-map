from sqlalchemy import inspect

from app.db.database import create_tables, engine, get_db
from app.models.affiliate import AffiliateBroker, AffiliateClick

print("--- Starting Database Verification ---")

# 1. Create tables
try:
    create_tables()
    print("✓ Step 1: create_tables() executed successfully.")
except Exception as e:
    print(f"✗ Step 1 Failed: Error during table creation: {e}")
    exit(1)


# 2. Verify table creation
try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  - Found tables: {tables}")
    assert "affiliate_brokers" in tables
    assert "affiliate_clicks" in tables
    print("✓ Step 2: Verified that 'affiliate_brokers' and 'affiliate_clicks' tables exist.")
except Exception as e:
    print(f"✗ Step 2 Failed: Error during table verification: {e}")
    exit(1)


# 3. Test database connection via get_db()
try:
    db_generator = get_db()
    with next(db_generator) as db:
        assert db is not None
        # Perform a simple query to ensure the connection is live
        db.query(AffiliateBroker).first()
    print("✓ Step 3: Database connection via get_db() successful.")
except Exception as e:
    print(f"✗ Step 3 Failed: Error during get_db() connection test: {e}")
    exit(1)

print("\n--- Database Verification Succeeded! ---")
