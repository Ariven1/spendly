# Spec: Registration

## Overview

Make the existing `/register` page functional. Today `GET /register` only renders a form that posts to `/register`, but no handler accepts the POST. This step adds server-side validation, password hashing, and insertion of a new row into the `users` table, so visitors can create a Spendly account. It builds directly on the data layer from Step 1 and is the prerequisite for login (Step 3).
  
## Depends on

- Step 01 — Database setup (`users` table, `get_db()`, `init_db()`)

## Routes

- `GET /register` — render the registration form — public (already exists, unchanged)
- `POST /register` — validate the form, create the user, redirect to `/login` on success or re-render the form with an error — public

## Database changes

No database changes. The `users` table in `database/db.py` already has `name`, `email` (UNIQUE), `password_hash` and `created_at`.

## Templates

- Create: none
- Modify:
  - `templates/register.html` — repopulate the `name` and `email` inputs from submitted values on error (never the password); keep the existing `error` block

## Files to change

- `app.py` — change the `/register` route to accept `GET` and `POST`, add the validation and insert logic
- `templates/register.html` — repopulate fields after a failed submission

## Files to create

- None

## New dependencies

No new dependencies. Uses `werkzeug.security` (already installed) and `sqlite3`.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only; never use string formatting in SQL
- Passwords hashed with werkzeug (`generate_password_hash(password, method="pbkdf2:sha256")`, matching `seed_db()`; the default scrypt method is unavailable in some Python builds)
- Use CSS variables; never hardcode hex values
- All templates extend `base.html`
- Use `get_db()` from `database/db.py`, and close the connection in a `finally` block
- Trim whitespace from `name` and `email`; store `email` lowercased
- Validation, in order, each failure re-rendering `register.html` with an `error` message and HTTP 400:
  - `name`, `email` and `password` are all non-empty
  - `email` contains `@` with text on both sides
  - `password` is at least 8 characters (matches the form placeholder)
  - `confirm_password` matches `password` ("Passwords do not match.")
- Duplicate email: check with a `SELECT` and also catch `sqlite3.IntegrityError` on insert, so a race cannot cause a 500. Show "An account with this email already exists." Do not reveal anything else about the existing account
- Never log or echo the password, and never put it back into the form
- On success, redirect (`303`/`302`) to `url_for("login")`. Do not start a session; login arrives in Step 3
- Do not add `flask.flash` or a `secret_key` in this step

## Definition of done

- [ ] `GET /register` still renders the form with status 200
- [ ] Submitting valid details creates a row in `users`, with `password_hash` set and not equal to the plain password
- [ ] After a successful submit the browser lands on `/login`
- [ ] `created_at` is populated on the new row
- [ ] Submitting an email that already exists (e.g. `demo@spendly.com`) shows the duplicate-email error, creates no row, and keeps the typed name and email
- [ ] The same email in different letter case (`Demo@Spendly.com`) is also rejected
- [ ] A password shorter than 8 characters shows an error and creates no row
- [ ] A missing name, email or password (form bypassing the `required` attribute) shows an error and creates no row
- [ ] An invalid email such as `abc` shows an error and creates no row
- [ ] The password field is empty after any failed submit
- [ ] The stored hash verifies with `check_password_hash` against the submitted password
- [ ] The app starts with no errors and the other routes are unaffected
