"""SQLite storage helpers. All queries are parameterized."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

DB_PATH = Path(__file__).parent / "data" / "cornprofit.db"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, contact TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, municipality TEXT DEFAULT '', barangay TEXT DEFAULT '',
 farm_name TEXT DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS farm_records (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, crop_type TEXT DEFAULT 'Corn',
 planting_date TEXT, harvest_date TEXT, location TEXT, area_ha REAL, expected_kg REAL DEFAULT 0,
 actual_kg REAL DEFAULT 0, notes TEXT, status TEXT DEFAULT 'planned', created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS expenses (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, farm_id INTEGER, date TEXT NOT NULL,
 category TEXT NOT NULL, description TEXT NOT NULL, quantity REAL, unit TEXT, unit_price REAL,
 amount REAL NOT NULL CHECK(amount >= 0), supplier TEXT, notes TEXT,
 FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(farm_id) REFERENCES farm_records(id)
);
CREATE TABLE IF NOT EXISTS income (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, farm_id INTEGER, date TEXT NOT NULL,
 quantity_kg REAL DEFAULT 0, price_per_kg REAL DEFAULT 0, gross_sales REAL NOT NULL DEFAULT 0,
 other_income REAL NOT NULL DEFAULT 0, buyer TEXT, notes TEXT,
 FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(farm_id) REFERENCES farm_records(id)
);
CREATE TABLE IF NOT EXISTS budgets (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, farm_id INTEGER, name TEXT NOT NULL,
 capital REAL NOT NULL DEFAULT 0, emergency_allowance REAL NOT NULL DEFAULT 0, expected_kg REAL DEFAULT 0,
 expected_price REAL DEFAULT 0, created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(farm_id) REFERENCES farm_records(id)
);
CREATE TABLE IF NOT EXISTS budget_items (
 id INTEGER PRIMARY KEY AUTOINCREMENT, budget_id INTEGER NOT NULL, category TEXT NOT NULL,
 quantity REAL DEFAULT 0, unit TEXT, unit_cost REAL DEFAULT 0, total REAL NOT NULL DEFAULT 0,
 FOREIGN KEY(budget_id) REFERENCES budgets(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS price_reports (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, product TEXT NOT NULL, category TEXT NOT NULL,
 brand TEXT, package_size REAL DEFAULT 1, unit TEXT DEFAULT 'kg', price REAL NOT NULL CHECK(price >= 0),
 supplier TEXT, location TEXT, reported_at TEXT NOT NULL, verified_at TEXT, verification TEXT DEFAULT 'Unverified',
 notes TEXT, FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS price_alerts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, product TEXT NOT NULL,
 target_price REAL NOT NULL, condition TEXT NOT NULL DEFAULT 'at or below', active INTEGER DEFAULT 1,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS farmer_listings (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, display_name TEXT NOT NULL, location TEXT,
 expected_kg REAL NOT NULL DEFAULT 0, harvest_date TEXT, arrangement TEXT, quality TEXT, contact TEXT,
 status TEXT DEFAULT 'Open', updated_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS connection_requests (
 id INTEGER PRIMARY KEY AUTOINCREMENT, from_user INTEGER NOT NULL, to_user INTEGER NOT NULL,
 listing_id INTEGER, status TEXT DEFAULT 'Pending', created_at TEXT NOT NULL,
 FOREIGN KEY(from_user) REFERENCES users(id), FOREIGN KEY(to_user) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS group_plans (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, buyer TEXT,
 price_per_kg REAL DEFAULT 0, transport_cost REAL DEFAULT 0, payment_terms TEXT, quality_requirements TEXT,
 created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS group_members (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, farmer_name TEXT NOT NULL,
 quantity_kg REAL NOT NULL DEFAULT 0, agreed INTEGER DEFAULT 0,
 FOREIGN KEY(plan_id) REFERENCES group_plans(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS buyer_offers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, buyer TEXT NOT NULL, location TEXT,
 price_per_kg REAL NOT NULL DEFAULT 0, min_kg REAL DEFAULT 0, max_kg REAL DEFAULT 0,
 corn_type TEXT, moisture TEXT, fixed_deduction REAL DEFAULT 0, percent_deduction REAL DEFAULT 0,
 payment_terms TEXT, delivery TEXT, expires TEXT, updated_at TEXT NOT NULL,
 verification TEXT DEFAULT 'Unverified', contact TEXT, notes TEXT,
 FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS saved_offers (
 user_id INTEGER NOT NULL, offer_id INTEGER NOT NULL, contacted INTEGER DEFAULT 0,
 PRIMARY KEY(user_id, offer_id), FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(offer_id) REFERENCES buyer_offers(id)
);
CREATE TABLE IF NOT EXISTS transport_estimates (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, offer_id INTEGER, distance_km REAL DEFAULT 0,
 liters_per_km REAL DEFAULT 0, fuel_price REAL DEFAULT 0, loading REAL DEFAULT 0, tolls REAL DEFAULT 0,
 other REAL DEFAULT 0, hired_fee REAL, total REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(offer_id) REFERENCES buyer_offers(id)
);
CREATE TABLE IF NOT EXISTS cost_allocations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, farmer_name TEXT NOT NULL,
 quantity_kg REAL NOT NULL, assigned_cost REAL NOT NULL, proceeds REAL NOT NULL,
 FOREIGN KEY(plan_id) REFERENCES group_plans(id) ON DELETE CASCADE
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con:
        con.executescript(SCHEMA)

@contextmanager
def db():
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def now_text():
    return datetime.now().isoformat(timespec="minutes")
