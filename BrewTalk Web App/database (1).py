# database.py
import sqlite3
import json
from typing import List, Tuple, Any, Dict, Optional
import config  # Import our config file

# Point to the database name from config
DB_NAME = config.DB_NAME

def get_db_connection():
    """Gets a connection to the SQLite database."""
    # We will name the database file based on our config
    # PythonAnywhere will create this file in your main folder
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Create database tables and seed with initial menu items if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS initial_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            in_stock BOOLEAN NOT NULL DEFAULT 1,
            image TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            items TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    ''')

    # ----- INSERT INITIAL MENU ITEMS -----
    cursor.execute('SELECT COUNT(*) FROM initial_items')
    if cursor.fetchone()[0] == 0:
        initial_items = [
            ('Cappuccino', 150.0, 1, 'cappuccino.jpg'),
            ('Latte', 160.0, 1, 'latte.jpg'),
            ('Americano', 140.0, 1, 'americano.jpg'),
            ('Mocha', 180.0, 1, 'mocha.jpg'),
            ('Frappe', 200.0, 1, 'frappe.jpg'),
            ('Cheesecake', 250.0, 1, 'cheesecake.jpg'),
            ('Pastry', 120.0, 1, 'pastry.jpg'),
            ('Brownie', 100.0, 1, 'brownie.jpg'),
            ('Vegetable Sandwich', 180.0, 1, 'veg_sandwich.jpg'),
            ('Grilled Cheese Sandwich', 200.0, 1, 'grilled_cheese.jpg'),
            ('Croissant', 80.0, 1, 'croissant.jpg'),
            ('Cookies', 60.0, 1, 'cookies.jpg')
        ]
        cursor.executemany(
            "INSERT INTO initial_items (name, price, in_stock, image) VALUES (?, ?, ?, ?)",
            initial_items
        )

    conn.commit()
    conn.close()

def get_menu_items() -> List[sqlite3.Row]:
    """Fetch all menu items from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM initial_items ORDER BY name')
    items = cursor.fetchall()
    conn.close()
    return items

def get_pending_orders_count() -> int:
    """Count how many orders are still 'Pending'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_menu_item(name: str, price: float, in_stock: bool) -> Tuple[bool, str]:
    """Adds a new item to the menu. Returns (success, message)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO initial_items (name, price, in_stock) VALUES (?, ?, ?)',
                       (name, price, in_stock))
        conn.commit()
        return (True, f"Added {name} to menu!")
    except sqlite3.IntegrityError:
        return (False, f"Item '{name}' already exists!")
    finally:
        conn.close()

def process_new_order(form_data: Dict) -> Optional[float]:
    """Processes form data to create an order. Returns total price or None."""
    items = []
    total = 0.0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM initial_items")
    menu = {item['id']: item for item in cursor.fetchall()}
    conn.close()

    for item_id, item_details in menu.items():
        check_name = f"item_{item_id}"
        qty_name = f"qty_{item_id}"

        if check_name in form_data:
            try:
                qty = int(form_data.get(qty_name, 1))
                if qty > 0:
                    items.append({"name": item_details["name"], "qty": qty})
                    total += item_details["price"] * qty
            except ValueError:
                continue # Ignore invalid quantity

    if not items:
        return None  # No valid items selected

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO orders (items, total_price, status) VALUES (?, ?, ?)',
        (json.dumps(items), total, 'Pending')
    )
    conn.commit()
    conn.close()
    return total

def get_pending_orders() -> List[sqlite3.Row]:
    """Fetches all pending orders."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status = 'Pending'")
    pending_orders = cursor.fetchall()
    conn.close()
    return pending_orders

def mark_order_complete(order_id: int) -> None:
    """Updates an order status to 'Completed'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status='Completed' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()