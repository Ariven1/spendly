import pytest
from werkzeug.security import generate_password_hash

import database.db as db

DEMO_EMAIL = "demo@spendly.com"
DEMO_PASSWORD = "demo123"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at a fresh, seeded temporary database (never spendly.db)."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    db.seed_db()
    yield


@pytest.fixture
def app(temp_db):
    # Imported after DB_PATH is patched so the module-level init_db/seed_db
    # never touches the real database on first import.
    from app import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo_user_id():
    conn = db.get_db()
    try:
        return conn.execute("SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)).fetchone()["id"]
    finally:
        conn.close()


@pytest.fixture
def empty_user_id():
    conn = db.get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Empty User", "empty@spendly.com", generate_password_hash("password123", method="pbkdf2:sha256")),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def login(client, email=DEMO_EMAIL, password=DEMO_PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


@pytest.fixture
def demo_client(client):
    login(client)
    return client


@pytest.fixture
def empty_client(client, empty_user_id):
    login(client, "empty@spendly.com", "password123")
    return client
