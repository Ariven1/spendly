# Spec: Profile Page Design

## Overview

Replace the `/profile` placeholder string with a real, designed page. Steps 2 and 3 let a user register and sign in, and both flows already redirect to `/profile`, but it still returns "Profile page — coming in Step 4". This step builds the signed-in landing page: an account header (name, email, member-since), summary stat tiles (total spent, this month, number of expenses, top category), a category breakdown, and a recent-expenses list, all read from the existing `users` and `expenses` tables. It also makes `/profile` the first route that requires a signed-in user. The visual design matches the existing warm-paper, green-accent style in `static/css/style.css`.

## Depends on

- Step 01 — Database setup (`users` and `expenses` tables, `get_db()`, demo seed data)
- Step 02 — Registration
- Step 03 — Login and logout (`session["user_id"]`, `session["user_name"]`, navbar with "Profile" link)

## Routes

- `GET /profile` — render the profile page for the current user; redirect to `/login` if not signed in — logged-in (exists as a placeholder, modify)

No other new routes. The expense add/edit/delete placeholders stay untouched (Steps 7–9).

## Database changes

No database changes. `users` (`id`, `name`, `email`, `created_at`) and `expenses` (`user_id`, `amount`, `category`, `date`, `description`) already hold everything the page shows. Verified against `database/db.py`.

## Templates

- Create:
  - `templates/profile.html` — extends `base.html`; sections: profile header, stat tiles, category breakdown, recent expenses, empty state
- Modify:
  - none (`base.html` already links to `url_for('profile')`)

### Page layout

1. **Profile header** — circular avatar showing the user's initials, name in `--font-display`, email in `--ink-muted`, "Member since <Month YYYY>" from `users.created_at`.
2. **Stat tiles (4-up grid)** — Total spent, Spent this month, Number of expenses, Top category. Amounts shown as `₹1,234.50` (the site copy uses rupees).
3. **Category breakdown** — one row per category: label, amount, share of total as a percent, and a horizontal bar sized by that share. Sorted by amount, highest first.
4. **Recent expenses** — the 8 most recent expenses (by `date` desc, then `id` desc): date, description, category pill, amount right-aligned. If the user has more, no pagination yet.
5. **Empty state** — when the user has no expenses: a short message and a disabled-looking "Add expense" link to `url_for('add_expense')`. Stat tiles show `₹0.00` / `0` / `—`, and the breakdown and list are replaced by the empty state.

Responsive: tiles go 4 → 2 → 1 columns; the recent list stacks the date under the description on narrow screens. Side gutters stay at least 16px.

## Files to change

- `app.py` — replace the `profile()` placeholder with a real view: guard on session, query the user and their expenses, pass computed values to the template
- `static/css/style.css` — add profile page styles (all colours from existing CSS variables)

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs
- Parameterised queries only; never use string formatting in SQL
- Passwords hashed with werkzeug (this step never reads or displays `password_hash`; do not select it)
- Use CSS variables; never hardcode hex values. Existing hardcoded hex in the landing styles is not a pattern to copy. If a needed colour is missing, add a variable to `:root` first
- All templates extend `base.html`
- Use `get_db()` from `database/db.py` and close the connection in a `finally` block
- Every query filters on `session["user_id"]`. A user must never see another user's expenses
- If `session.get("user_id")` is missing, `redirect(url_for("login"))`. If the user id is in the session but no row exists, `session.clear()` and redirect to login
- Aggregate in SQL (`SUM`, `COUNT`, `GROUP BY`), not by looping over all rows in Python
- "This month" is the current calendar month, matched with `strftime('%Y-%m', date) = ?` and a parameter computed in Python
- Compute category percentages in the view; guard against division by zero when total is 0
- Format money with a small Jinja filter or view-side formatting: 2 decimals, thousands separators, `₹` prefix. Do not use `|safe` on any user-supplied field (`description`, `category`, `name`) — rely on Jinja autoescaping
- Category pill colours must come from CSS variables, with one neutral fallback for unknown categories
- Do not add expense CRUD, filters, charts libraries, JS frameworks, or profile editing in this step
- Do not change login, logout or registration behaviour
- Follow the existing CSS conventions: section header comment blocks, class names prefixed `profile-`

## Definition of done

- [ ] Signed out, visiting `/profile` redirects to `/login`
- [ ] Logging in as `demo@spendly.com` / `demo123` lands on a rendered profile page with status 200, not the placeholder text
- [ ] The header shows "Demo User", `demo@spendly.com`, initials "DU", and a "Member since" month and year
- [ ] For the seeded demo data, Total spent is `₹346.24`, Number of expenses is `8`, and Top category is `Bills`
- [ ] "Spent this month" equals the sum of expenses dated in the current month
- [ ] The category breakdown lists all 7 seeded categories, sorted by amount descending, and the percentages add up to about 100%
- [ ] The recent list shows the expenses newest first, with date, description, category and amount
- [ ] A newly registered user with no expenses sees the empty state, with `₹0.00` and `0` tiles and no errors
- [ ] A second user's profile never shows the demo user's expenses
- [ ] An expense description containing `<script>alert(1)</script>` is shown as text and does not execute
- [ ] The layout works at 1200px, 768px and 375px widths with no horizontal scroll
- [ ] `grep -nE '#[0-9a-fA-F]{3,6}' templates/profile.html` returns nothing, and the new CSS block adds no hex values outside `:root`
- [ ] The navbar still shows the user's name, "Profile" and "Sign out" while on the page, and "Sign out" still works
- [ ] The app starts with no errors and the other routes are unaffected
