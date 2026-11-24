from database.queries import get_user_by_id


# ------------------------------------------------------------------ #
# Shared: user lookup and route basics                                #
# ------------------------------------------------------------------ #

def test_get_user_by_id_valid(demo_user_id):
    user = get_user_by_id(demo_user_id)
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    # "Month YYYY", e.g. "November 2026"
    month, year = user["member_since"].split()
    assert month.isalpha() and len(year) == 4 and year.isdigit()
    assert "password_hash" not in user


def test_get_user_by_id_missing():
    assert get_user_by_id(999999) is None


def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_shows_user_info(demo_client):
    resp = demo_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Demo User" in html
    assert "demo@spendly.com" in html
    assert "₹" in html


def test_profile_empty_user_no_errors(empty_client):
    resp = empty_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "₹0.00" in html
    assert "No expenses yet" in html


# ---- Transactions Tests ----
SEED_DESCRIPTIONS_NEWEST_FIRST = [
    "Dinner out",
    "Gift wrap and cards",
    "New sneakers",
    "Movie night",
    "Pharmacy",
    "Electricity bill",
    "Metro pass top-up",
    "Groceries",
]


def test_get_recent_transactions_demo_user(demo_user_id):
    from database.queries import get_recent_transactions

    items = get_recent_transactions(demo_user_id)
    assert len(items) == 8
    for item in items:
        for key in ("date", "description", "category", "amount"):
            assert key in item
    dates = [item["date"] for item in items]
    assert dates == sorted(dates, reverse=True)
    assert items[0]["description"] == "Dinner out"
    assert [i["description"] for i in items] == SEED_DESCRIPTIONS_NEWEST_FIRST


def test_get_recent_transactions_empty_user(empty_user_id):
    from database.queries import get_recent_transactions

    assert get_recent_transactions(empty_user_id) == []


def test_profile_route_renders_recent_transactions(demo_client):
    resp = demo_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    positions = []
    for desc in SEED_DESCRIPTIONS_NEWEST_FIRST:
        assert desc in html
        positions.append(html.index(desc))
    assert positions == sorted(positions)


# ---- Summary Stats Tests ----
def test_get_summary_stats_demo_user(demo_user_id):
    import pytest
    from database.queries import get_summary_stats

    stats = get_summary_stats(demo_user_id)
    assert stats["total_spent"] == pytest.approx(346.24)
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"
    assert stats["month_total"] == pytest.approx(346.24)


def test_get_summary_stats_month_without_data(demo_user_id):
    from database.queries import get_summary_stats

    stats = get_summary_stats(demo_user_id, month="1999-01")
    assert stats["month_total"] == 0
    assert stats["transaction_count"] == 8


def test_get_summary_stats_empty_user(empty_user_id):
    from database.queries import get_summary_stats

    assert get_summary_stats(empty_user_id) == {
        "total_spent": 0,
        "transaction_count": 0,
        "top_category": "—",
        "month_total": 0,
    }


def test_profile_route_renders_summary_stats(demo_client):
    resp = demo_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "₹346.24" in html
    assert "Bills" in html
    assert ">8<" in html


# ---- Category Breakdown Tests ----
SEED_CATEGORIES = ["Bills", "Shopping", "Food", "Health", "Entertainment", "Other", "Transport"]


def test_get_category_breakdown_demo_user(demo_user_id):
    import pytest
    from database.queries import get_category_breakdown

    items = get_category_breakdown(demo_user_id)
    assert len(items) == 7
    for item in items:
        for key in ("name", "slug", "amount", "pct"):
            assert key in item
        assert isinstance(item["pct"], int)
        assert item["slug"] == item["name"].lower()
    amounts = [item["amount"] for item in items]
    assert amounts == sorted(amounts, reverse=True)
    assert [item["name"] for item in items] == SEED_CATEGORIES
    assert items[0]["name"] == "Bills"
    assert items[0]["amount"] == pytest.approx(120.00)
    assert sum(item["pct"] for item in items) == 100


def test_get_category_breakdown_rounding_remainder(empty_user_id):
    from database.db import get_db
    from database.queries import get_category_breakdown

    conn = get_db()
    try:
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            [
                (empty_user_id, 1.00, "Food", "2026-11-01", "a"),
                (empty_user_id, 1.00, "Transport", "2026-11-02", "b"),
                (empty_user_id, 1.00, "Bills", "2026-11-03", "c"),
            ],
        )
        conn.commit()
    finally:
        conn.close()

    items = get_category_breakdown(empty_user_id)
    assert len(items) == 3
    # Naive rounding gives 33 + 33 + 33 = 99; the first item absorbs the remainder.
    assert sum(item["pct"] for item in items) == 100
    assert items[0]["pct"] == 34
    assert [item["pct"] for item in items[1:]] == [33, 33]


def test_get_category_breakdown_empty_user(empty_user_id):
    from database.queries import get_category_breakdown

    assert get_category_breakdown(empty_user_id) == []


def test_profile_route_renders_category_breakdown(demo_client):
    resp = demo_client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    for name in SEED_CATEGORIES:
        assert name in html
    assert "<meter" in html
    assert 'class="profile-meter profile-meter--bills"' in html
    assert "style=" not in html
