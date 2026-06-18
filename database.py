from werkzeug.security import generate_password_hash
import sqlite3
import os

DB_NAME = "/app/data/ecommerce.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    os.makedirs("/app/data", exist_ok=True)

    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------
    # Users Table
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    # -------------------------
    # Products Table
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            image TEXT
        )
    """)

    # -------------------------
    # Orders Table
    # Each order belongs to a user
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(id)
        )
    """)

    # -------------------------
    # Order Items Table
    # -------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,

            FOREIGN KEY(order_id)
            REFERENCES orders(id),

            FOREIGN KEY(product_id)
            REFERENCES products(id)
        )
    """)

    conn.commit()

    # -------------------------
    # Seed Products
    # -------------------------

    count = cursor.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        products = [

            (
                "Laptop",
                "High performance laptop with 16GB RAM",
                75000,
                10,
                "https://images.unsplash.com/photo-1496181133206-80ce9b88a853"
            ),

            (
                "Wireless Mouse",
                "Ergonomic wireless mouse",
                999,
                50,
                "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46"
            ),

            (
                "Mechanical Keyboard",
                "RGB Mechanical keyboard",
                3499,
                25,
                "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae"
            ),

            (
                "Monitor",
                "27 inch Full HD Monitor",
                12000,
                15,
                "https://images.unsplash.com/photo-1527443154391-507e9dc6c5cc"
            ),

            (
                "Headphones",
                "Noise cancelling headphones",
                4500,
                20,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
            )
        ]

        cursor.executemany("""
            INSERT INTO products
            (name, description, price, stock, image)
            VALUES (?, ?, ?, ?, ?)
        """, products)

        conn.commit()

    # -------------------------
    # Seed Admin User
    # -------------------------

    admin = cursor.execute(
        "SELECT * FROM users WHERE username=?",
        ("admin",)
    ).fetchone()

    if not admin:

        cursor.execute("""
            INSERT INTO users
            (username, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "admin",
            "admin@shopeasy.com",
            generate_password_hash("Admin@123"),
            "admin"
        ))

        conn.commit()

    conn.close()
