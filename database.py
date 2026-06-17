import sqlite3

DB_NAME = "/app/data/ecommerce.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Products table
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

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_amount REAL NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Order Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,

            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()

    # Seed sample products if database is empty
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
                "https://via.placeholder.com/250"
            ),
            (
                "Wireless Mouse",
                "Ergonomic wireless mouse",
                999,
                50,
                "https://via.placeholder.com/250"
            ),
            (
                "Mechanical Keyboard",
                "RGB Mechanical keyboard",
                3499,
                25,
                "https://via.placeholder.com/250"
            ),
            (
                "Monitor",
                "27 inch Full HD Monitor",
                12000,
                15,
                "https://via.placeholder.com/250"
            ),
            (
                "Headphones",
                "Noise cancelling headphones",
                4500,
                20,
                "https://via.placeholder.com/250"
            )
        ]

        cursor.executemany("""
            INSERT INTO products
            (name, description, price, stock, image)
            VALUES (?, ?, ?, ?, ?)
        """, products)

        conn.commit()

    conn.close()
