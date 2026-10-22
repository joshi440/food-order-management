
import os
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this")

DATABASE_PATH = os.environ.get("DATABASE_PATH", "orders.db")
ALLOWED_STATUSES = {"Pending", "Preparing", "Delivered", "Cancelled"}

DEFAULT_MENU = [
    ("Veg Burger", 99.00, "Burgers"),
    ("Margherita Pizza", 199.00, "Pizza"),
    ("Masala Dosa", 80.00, "Indian"),
    ("Veg Fried Rice", 140.00, "Rice"),
    ("Paneer Sandwich", 120.00, "Snacks"),
    ("French Fries", 79.00, "Snacks"),
]


def get_db():
    if DATABASE_PATH != ":memory:":
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK(price > 0),
                category TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                food_id INTEGER NOT NULL,
                food_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(food_id) REFERENCES menu(id)
                    ON DELETE RESTRICT
            );
        """)

        count = db.execute("SELECT COUNT(*) FROM menu").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO menu (name, price, category) VALUES (?, ?, ?)",
                DEFAULT_MENU,
            )


@app.route("/")
def index():
    with get_db() as db:
        menu = db.execute("SELECT * FROM menu ORDER BY name").fetchall()
        orders = db.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()

        stats = {
            "orders": db.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0],
            "pending": db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'Pending'"
            ).fetchone()[0],
            "revenue": db.execute(
                "SELECT COALESCE(SUM(total), 0) FROM orders "
                "WHERE status != 'Cancelled'"
            ).fetchone()[0],
        }

    return render_template(
        "index.html",
        menu=menu,
        orders=orders,
        stats=stats,
        statuses=sorted(ALLOWED_STATUSES),
    )


@app.route("/order", methods=["POST"])
def place_order():
    customer = request.form.get("customer_name", "").strip()
    food_id = request.form.get("food_id", type=int)
    quantity = request.form.get("quantity", type=int)

    if not customer or len(customer) > 80:
        flash("Enter a customer name (maximum 80 characters).", "error")
        return redirect(url_for("index"))

    if not food_id or not quantity or not 1 <= quantity <= 100:
        flash("Select a food item and a quantity from 1 to 100.", "error")
        return redirect(url_for("index"))

    with get_db() as db:
        food = db.execute(
            "SELECT * FROM menu WHERE id = ?", (food_id,)
        ).fetchone()

        if food is None:
            flash("That food item does not exist.", "error")
            return redirect(url_for("index"))

        unit_price = food["price"]
        total = round(unit_price * quantity, 2)

        db.execute(
            """INSERT INTO orders
               (customer_name, food_id, food_name, quantity,
                unit_price, total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (customer, food_id, food["name"], quantity, unit_price, total),
        )

    flash("Order placed successfully!", "success")
    return redirect(url_for("index"))


@app.route("/order/<int:order_id>/status", methods=["POST"])
def update_status(order_id):
    status = request.form.get("status", "")

    if status not in ALLOWED_STATUSES:
        flash("Invalid order status.", "error")
        return redirect(url_for("index"))

    with get_db() as db:
        result = db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )

    if result.rowcount == 0:
        flash("Order not found.", "error")
    else:
        flash("Order status updated.", "success")

    return redirect(url_for("index"))


@app.route("/order/<int:order_id>/delete", methods=["POST"])
def delete_order(order_id):
    with get_db() as db:
        result = db.execute(
            "DELETE FROM orders WHERE id = ?", (order_id,)
        )

    if result.rowcount == 0:
        flash("Order not found.", "error")
    else:
        flash("Order deleted.", "success")

    return redirect(url_for("index"))


@app.route("/api/health")
def health():
    try:
        with get_db() as db:
            db.execute("SELECT 1").fetchone()
        return jsonify({"status": "healthy"}), 200
    except sqlite3.Error:
        app.logger.exception("Database health check failed")
        return jsonify({"status": "unhealthy"}), 503


@app.route("/api/menu")
def menu_api():
    with get_db() as db:
        menu = db.execute("SELECT * FROM menu ORDER BY name").fetchall()
    return jsonify([dict(item) for item in menu])


@app.route("/api/orders")
def orders_api():
    with get_db() as db:
        orders = db.execute(
            "SELECT * FROM orders ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(order) for order in orders])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
