"""Read-only query helpers for the profile page.

Pure data access: no Flask imports. Every helper takes ``user_id`` explicitly,
opens its own connection via ``get_db()`` and closes it before returning.
"""

from datetime import date, datetime

from database.db import get_db

KNOWN_CATEGORIES = {"food", "transport", "bills", "health", "entertainment", "shopping", "other"}


def category_slug(category):
    slug = (category or "").lower()
    return slug if slug in KNOWN_CATEGORIES else "other"


def _format_member_since(created_at):
    try:
        return datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except (TypeError, ValueError):
        return None


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "member_since": _format_member_since(row["created_at"]),
    }


# ---- Transactions ----
def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "id": row["id"],
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
            "slug": category_slug(row["category"]),
        }
        for row in rows
    ]


# ---- Summary Stats ----
def get_summary_stats(user_id, month=None):
    if month is None:
        month = date.today().strftime("%Y-%m")
    conn = get_db()
    try:
        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total_spent, COUNT(*) AS transaction_count "
            "FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        top = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ? "
            "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        month_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS month_total FROM expenses "
            "WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, month),
        ).fetchone()
        return {
            "total_spent": totals["total_spent"],
            "transaction_count": totals["transaction_count"],
            "top_category": top["category"] if top else "—",
            "month_total": month_row["month_total"],
        }
    finally:
        conn.close()


# ---- Category Breakdown ----
def get_category_breakdown(user_id):
    """Per-category spend for a user, largest first, with integer percentages summing to 100."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    grand_total = sum(row["total"] for row in rows)
    if not rows or grand_total <= 0:
        return []

    breakdown = [
        {
            "name": row["category"],
            "slug": category_slug(row["category"]),
            "amount": round(row["total"], 2),
            "pct": int(round(row["total"] / grand_total * 100)),
        }
        for row in rows
    ]
    breakdown[0]["pct"] += 100 - sum(item["pct"] for item in breakdown)
    return breakdown
