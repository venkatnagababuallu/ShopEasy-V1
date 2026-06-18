from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import (
    get_connection,
    init_db
)

import os
import logging


# ----------------------------------
# App Configuration
# ----------------------------------

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "devops-secret-key"
)

init_db()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# ----------------------------------
# Home Page
# ----------------------------------

@app.route("/")
def index():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search")

    conn = get_connection()

    if search:

        products = conn.execute("""
            SELECT *
            FROM products
            WHERE
            name LIKE ?
            OR description LIKE ?
        """, (
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        products = conn.execute("""
            SELECT *
            FROM products
        """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        products=products
    )


# ----------------------------------
# Product Details
# ----------------------------------

@app.route("/product/<int:id>")
def product(id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """, (
        id,
    )).fetchone()

    conn.close()

    if not product:
        return render_template(
            "404.html"
        ), 404

    return render_template(
        "product.html",
        product=product
    )


# ----------------------------------
# Register
# ----------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = generate_password_hash(
            request.form["password"]
        )

        conn = get_connection()

        try:

            conn.execute("""
                INSERT INTO users
                (
                    username,
                    email,
                    password,
                    role
                )
                VALUES
                (
                    ?, ?, ?, ?
                )
            """, (
                username,
                email,
                password,
                "user"
            ))

            conn.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            conn.close()

            return redirect("/login")

        except Exception:

            conn.close()

            flash(
                "User already exists",
                "error"
            )

            return redirect("/register")

    return render_template(
        "register.html"
    )


# ----------------------------------
# Login
# ----------------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE username=?
        """, (
            username,
        )).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash(
                f"Welcome {username}!",
                "success"
            )

            logging.info(
                f"User logged in: {username}"
            )

            return redirect("/")

        flash(
            "Invalid username or password",
            "error"
        )

        return redirect("/login")

    return render_template(
        "login.html"
    )


# ----------------------------------
# Logout
# ----------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully",
        "success"
    )

    return redirect("/login")


# ----------------------------------
# Add To Cart
# ----------------------------------

@app.route("/add-to-cart/<int:id>")
def add(id):

    if "user_id" not in session:
        return redirect("/login")

    cart = session.get(
        "cart",
        {}
    )

    cart[str(id)] = cart.get(
        str(id),
        0
    ) + 1

    session["cart"] = cart

    flash(
        "Product added to cart",
        "success"
    )

    return redirect(
        url_for("cart")
    )


# ----------------------------------
# Cart
# ----------------------------------

@app.route("/cart")
def cart():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    items = []

    total = 0

    for pid, qty in session.get(
        "cart",
        {}
    ).items():

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE id=?
        """, (
            pid,
        )).fetchone()

        if product:

            subtotal = (
                product["price"] * qty
            )

            total += subtotal

            items.append(
                (
                    product,
                    qty,
                    subtotal
                )
            )

    conn.close()

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


# ----------------------------------
# Checkout
# ----------------------------------

@app.route("/checkout")
def checkout():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    cart = session.get(
        "cart",
        {}
    )

    if not cart:

        flash(
            "Your cart is empty",
            "error"
        )

        return redirect("/cart")

    total = 0

    for pid, qty in cart.items():

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE id=?
        """, (
            pid,
        )).fetchone()

        if product:

            total += (
                product["price"] * qty
            )

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders
        (
            user_id,
            total_amount
        )
        VALUES
        (
            ?, ?
        )
    """, (
        session["user_id"],
        total
    ))

    order_id = cursor.lastrowid

    for pid, qty in cart.items():

        product = conn.execute("""
            SELECT *
            FROM products
            WHERE id=?
        """, (
            pid,
        )).fetchone()

        if product:

            cursor.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    quantity,
                    price
                )
                VALUES
                (
                    ?, ?, ?, ?
                )
            """, (
                order_id,
                pid,
                qty,
                product["price"]
            ))

    conn.commit()
    conn.close()

    session["cart"] = {}

    flash(
        "Order placed successfully!",
        "success"
    )

    return redirect("/orders")

# ----------------------------------
# Orders
# ----------------------------------

@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()

    if session.get("role") == "admin":

        orders = conn.execute("""
            SELECT *
            FROM orders
            ORDER BY id DESC
        """).fetchall()

    else:

        orders = conn.execute("""
            SELECT *
            FROM orders
            WHERE user_id=?
            ORDER BY id DESC
        """, (
            session["user_id"],
        )).fetchall()

    conn.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# ----------------------------------
# Admin Dashboard
# ----------------------------------

@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return "Access Denied", 403

    conn = get_connection()

    products = conn.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        products=products
    )


# ----------------------------------
# Add Product
# ----------------------------------

@app.route(
    "/admin/add",
    methods=["GET", "POST"]
)
def addp():

    if session.get("role") != "admin":
        return "Access Denied", 403

    if request.method == "POST":

        conn = get_connection()

        conn.execute("""
            INSERT INTO products
            (
                name,
                description,
                price,
                stock,
                image
            )
            VALUES
            (
                ?, ?, ?, ?, ?
            )
        """, (
            request.form["name"],
            request.form["description"],
            request.form["price"],
            request.form["stock"],
            request.form["image"]
        ))

        conn.commit()
        conn.close()

        flash(
            "Product added successfully!",
            "success"
        )

        return redirect("/admin")

    return render_template(
        "add_product.html"
    )


# ----------------------------------
# Edit Product
# ----------------------------------

@app.route(
    "/admin/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_product(id):

    if session.get("role") != "admin":
        return "Access Denied", 403

    conn = get_connection()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id=?
    """, (
        id,
    )).fetchone()

    if not product:

        conn.close()

        return render_template(
            "404.html"
        ), 404

    if request.method == "POST":

        conn.execute("""
            UPDATE products
            SET
                name=?,
                description=?,
                price=?,
                stock=?,
                image=?
            WHERE id=?
        """, (
            request.form["name"],
            request.form["description"],
            request.form["price"],
            request.form["stock"],
            request.form["image"],
            id
        ))

        conn.commit()
        conn.close()

        flash(
            "Product updated successfully!",
            "success"
        )

        return redirect("/admin")

    conn.close()

    return render_template(
        "edit_product.html",
        product=product
    )


# ----------------------------------
# Delete Product
# ----------------------------------

@app.route("/admin/delete/<int:id>")
def delete_product(id):

    if session.get("role") != "admin":
        return "Access Denied", 403

    conn = get_connection()

    conn.execute("""
        DELETE FROM products
        WHERE id=?
    """, (
        id,
    ))

    conn.commit()
    conn.close()

    flash(
        "Product deleted successfully!",
        "success"
    )

    return redirect("/admin")


# ----------------------------------
# Health Endpoint
# ----------------------------------

@app.route("/health")
def health():

    return {
        "status": "UP"
    }


# ----------------------------------
# Version Endpoint
# ----------------------------------

@app.route("/version")
def version():

    return {
        "version": "1.3.0"
    }


# ----------------------------------
# Metrics Endpoint
# ----------------------------------

@app.route("/metrics")
def metrics():

    conn = get_connection()

    product_count = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    user_count = conn.execute("""
        SELECT COUNT(*)
        FROM users
    """).fetchone()[0]

    order_count = conn.execute("""
        SELECT COUNT(*)
        FROM orders
    """).fetchone()[0]

    conn.close()

    return f"""
product_count {product_count}
user_count {user_count}
order_count {order_count}
"""


# ----------------------------------
# Custom 404 Page
# ----------------------------------

@app.errorhandler(404)
def not_found(error):

    return render_template(
        "404.html"
    ), 404


# ----------------------------------
# Custom 500 Page
# ----------------------------------

@app.errorhandler(500)
def internal_error(error):

    return render_template(
        "500.html"
    ), 500


# ----------------------------------
# Main
# ----------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
