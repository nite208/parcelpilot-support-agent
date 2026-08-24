import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_orders_for_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE account_id = ?", (account_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_order(order_id, account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE order_id = ? AND account_id = ?",
        (order_id, account_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_order_internal(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_tickets_for_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE account_id = ?", (account_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ticket(ticket_id, account_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if account_id:
        cursor.execute(
            "SELECT * FROM tickets WHERE ticket_id = ? AND account_id = ?",
            (ticket_id, account_id)
        )
    else:
        cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_open_tickets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE status != 'CLOSED'")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_account_by_order(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT a.* FROM accounts a JOIN orders o ON a.account_id = o.account_id WHERE o.order_id = ?",
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def search_tickets_by_keyword(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE description LIKE ? OR resolution LIKE ?",
        (f"%{keyword}%", f"%{keyword}%")
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]