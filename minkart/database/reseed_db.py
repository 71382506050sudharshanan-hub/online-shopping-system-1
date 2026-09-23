import os
import sqlite3
from seed_data import SAMPLE_PRODUCTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")

def reseed():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop products table if exists to re-seed cleanly
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            discount_percentage INTEGER DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            rating REAL DEFAULT 4.5,
            review_count INTEGER DEFAULT 0,
            image_url TEXT,
            sku TEXT UNIQUE NOT NULL,
            featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for p in SAMPLE_PRODUCTS:
        cursor.execute("""
            INSERT INTO products (
                name, description, category, brand, price, original_price,
                discount_percentage, stock, rating, review_count, image_url, sku, featured
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["name"], p["description"], p["category"], p["brand"],
            p["price"], p["original_price"], p["discount_percentage"],
            p["stock"], p["rating"], p["review_count"],
            p["image_url"], p["sku"], p["featured"]
        ))

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    print(f"Successfully re-seeded products table! Total items in DB: {count}")
    conn.close()

if __name__ == "__main__":
    reseed()
