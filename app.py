import os
import sqlite3
from datetime import date, datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

with app.app_context():
    init_db()
    seed_db()

KNOWN_CATEGORIES = {"food", "transport", "bills", "health", "entertainment", "shopping", "other"}


def _category_slug(category):
    slug = (category or "").lower()
    return slug if slug in KNOWN_CATEGORIES else "other"


@app.template_filter("inr")
def inr(value):
    return f"₹{value or 0:,.2f}"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    def fail(error):
        return render_template("register.html", error=error, name=name, email=email), 400

    if not name or not email or not password:
        return fail("All fields are required.")

    local, _, domain = email.partition("@")
    if not local or not domain or "@" in domain:
        return fail("Please enter a valid email address.")

    if len(password) < 8:
        return fail("Password must be at least 8 characters.")

    if password != confirm_password:
        return fail("Passwords do not match.")

    conn = get_db()
    try:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return fail("An account with this email already exists.")
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password, method="pbkdf2:sha256")),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return fail("An account with this email already exists.")
    finally:
        conn.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    def fail(error, status):
        return render_template("login.html", error=error, email=email), status

    if not email or not password:
        return fail("Email and password are required.", 400)

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return fail("Invalid email or password.", 401)

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    this_month = date.today().strftime("%Y-%m")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            session.clear()
            return redirect(url_for("login"))

        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS n"
            " FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        month_total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
            " WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, this_month),
        ).fetchone()[0]
        category_rows = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses"
            " WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,),
        ).fetchall()
        recent = conn.execute(
            "SELECT id, date, description, category, amount FROM expenses"
            " WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 8",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    grand_total = totals["total"]
    categories = [
        {
            "name": row["category"],
            "slug": _category_slug(row["category"]),
            "total": row["total"],
            "pct": round(row["total"] / grand_total * 100) if grand_total else 0,
        }
        for row in category_rows
    ]
    recent_expenses = [
        {**dict(row), "slug": _category_slug(row["category"])} for row in recent
    ]

    parts = user["name"].split()
    if len(parts) > 1:
        initials = (parts[0][0] + parts[-1][0]).upper()
    else:
        initials = user["name"][:2].upper()

    try:
        member_since = datetime.strptime(
            user["created_at"], "%Y-%m-%d %H:%M:%S"
        ).strftime("%B %Y")
    except (TypeError, ValueError):
        member_since = None

    return render_template(
        "profile.html",
        user=user,
        initials=initials,
        member_since=member_since,
        total_spent=grand_total,
        month_total=month_total,
        expense_count=totals["n"],
        top_category=categories[0]["name"] if categories else None,
        categories=categories,
        recent_expenses=recent_expenses,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
