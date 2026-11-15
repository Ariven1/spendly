# Spec: Login and Logout

## Overview

Make sign-in and sign-out work. Step 2 lets visitors create accounts, but `GET /login` only renders a form whose POST has no handler, and `/logout` is a placeholder string. This step authenticates a user against the `users` table, keeps them signed in with a Flask session, and lets them sign out. It also makes the navbar reflect the signed-in state. Every later feature (profile, expenses) depends on knowing who the current user is, so this step introduces the session.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (users with hashed passwords can be created; registration redirects to `/login`)

## Routes

- `GET /login` — render the sign-in form; if already signed in, redirect to `/profile` — public (exists, modify)
- `POST /login` — validate credentials, start the session, redirect to `/profile` on success or re-render the form with an error — public (new method on the existing route)
- `POST /logout` — clear the session and redirect to `/` — logged-in (exists as a GET placeholder; change to POST only)

`/profile` is still a placeholder until Step 4, so a successful login lands on its placeholder text.

## Database changes

No database changes. `users` already has `email`, `password_hash` and `name`, which is everything login needs. Verified against `database/db.py`.

## Templates

- Create: none
- Modify:
  - `templates/login.html` — repopulate the `email` input from the submitted value on error (never the password); keep the existing `error` block
  - `templates/base.html` — navbar shows "Sign in" / "Get started" when signed out; when signed in, shows the user's name, a "Profile" link and a "Sign out" button (a small `<form method="POST" action="{{ url_for('logout') }}">`, styled like the other nav links)

## Files to change

- `app.py` — set `app.secret_key`, add the `POST` handler for `/login`, make `/logout` POST-only and clear the session
- `templates/login.html` — repopulate email after a failed attempt
- `templates/base.html` — conditional navbar based on `session`
- `static/css/style.css` — style for the "Sign out" button so it looks like a nav link (CSS variables only)

## Files to create

- None

## New dependencies

No new dependencies. Uses Flask's built-in `session` and `werkzeug.security.check_password_hash`.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only; never use string formatting in SQL
- Passwords hashed with werkzeug; verify with `check_password_hash`, never compare plain text or hashes by hand
- Use CSS variables; never hardcode hex values
- All templates extend `base.html`
- Use `get_db()` from `database/db.py`, and close the connection in a `finally` block
- `app.secret_key` comes from the `SECRET_KEY` environment variable, with a clearly named development fallback so the app still starts locally. Never commit a real secret
- Look the user up by `email.strip().lower()`, matching how registration stores it
- Use one generic error for both an unknown email and a wrong password: "Invalid email or password." Never reveal which part was wrong. Failures re-render `login.html` with HTTP 401, the typed email kept and the password never echoed
- Empty email or password re-renders with HTTP 400 and "Email and password are required."
- On success: call `session.clear()` first, then store `user_id` and `user_name`, then redirect (302/303) to `url_for("profile")`. Do not put the password hash in the session
- Logout is `POST` only and calls `session.clear()`, then redirects to `url_for("landing")`. Do not leave `GET /logout` working
- Set `SESSION_COOKIE_HTTPONLY = True` and `SESSION_COOKIE_SAMESITE = "Lax"`
- Do not add `flask.flash`, "remember me", password reset, or route-protection decorators in this step
- Do not change the registration behaviour, apart from what the navbar change implies

## Definition of done

- [ ] `GET /login` renders the form with status 200 when signed out
- [ ] Logging in as `demo@spendly.com` / `demo123` redirects to `/profile`
- [ ] The email match is case-insensitive and ignores surrounding spaces (`  DEMO@spendly.com `)
- [ ] After login, the navbar shows the user's name and a "Sign out" button, and no longer shows "Sign in" / "Get started"
- [ ] A wrong password shows "Invalid email or password." with status 401, keeps the typed email, and leaves the password field empty
- [ ] An unknown email shows the same message, with no difference in wording
- [ ] Submitting an empty email or password shows the required-fields error
- [ ] The session cookie is set on login and removed on logout
- [ ] Clicking "Sign out" lands on `/` with the signed-out navbar
- [ ] `GET /logout` returns 405
- [ ] Visiting `/login` while signed in redirects to `/profile`
- [ ] A user registered through `/register` can log in with the same credentials
- [ ] The app starts with no `SECRET_KEY` set, and the other routes are unaffected
