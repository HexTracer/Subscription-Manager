

Subscription Manager is a web app that helps a person keep track of every recurring payment they've signed up for — Netflix, Spotify, iCloud storage, a gym membership, a cloud server, whatever it is — in one place. It was built as my CS50x final project, using the same core stack the course teaches: Flask, SQLite, Jinja templates, and plain HTML/CSS, no JavaScript frameworks.

## Why this project

It's genuinely easy to lose track of how much money is quietly leaving your account every month across a dozen small subscriptions. Each one feels cheap on its own, but added together they often aren't. I wanted a tool that does three things well: show me one honest number for what all my subscriptions cost per month, warn me before something is about to renew, and make it trivial to add, edit, or cancel something without digging through email receipts. That's the entire scope of this project — I kept it deliberately narrow so that everything in it works properly, rather than building a longer feature list half-heartedly.

## How it works

A user registers for an account, logs in, and lands on a dashboard. The dashboard shows three numbers at the top — total monthly cost, total yearly cost, and how many active subscriptions exist — followed by a table listing every subscription: its name, category, cost, billing cycle, and next renewal date. Any subscription renewing within the next 7 days is visually flagged with a small dot and a "due soon" badge, so the most time-sensitive information is the easiest to notice, not buried in a long list.

From the dashboard, a user can:
- **Add** a new subscription (name, category, cost, monthly/yearly cycle, next renewal date, optional notes)
- **Edit** any existing subscription
- **Renew** a subscription with one click, which automatically pushes its next renewal date forward by one full cycle
- **Cancel** (delete) a subscription entirely

## Files

**`app.py`** is the heart of the application — every Flask route lives here. It handles user registration and login (with hashed passwords via Werkzeug), the dashboard, and full CRUD (create, read, update, delete) for subscriptions, plus the "renew" action. It also creates the SQLite database and its two tables (`users` and `subscriptions`) automatically the first time it runs, so there's no manual setup step beyond installing dependencies.

**`helpers.py`** holds three small utilities kept out of `app.py` to keep the routes file readable: `login_required`, a decorator that redirects anyone who isn't logged in; `apology`, which renders a simple error page instead of crashing or failing silently; and `monthly_equivalent`, the one piece of real "business logic" in the app — it converts a yearly subscription's cost into a monthly figure so that a $9.99/month plan and a $120/year plan can be added into one honest total instead of being compared apples-to-oranges.

**`templates/`** contains all the Jinja templates: `layout.html` (the shared navbar and page shell), `login.html`, `register.html`, `index.html` (the dashboard), `add.html` and `edit.html` (the subscription forms, which share almost identical markup), and `apology.html` (the error page).

**`static/styles.css`** holds all of the app's styling — a warm white-and-brandy color palette, paired with the Fraunces and Inter typefaces for a slightly warmer, less generic look than default Bootstrap styling.

**`requirements.txt`** lists the two dependencies: Flask and Werkzeug.

## Design decisions

**SQLite via Python's built-in `sqlite3` module, not the CS50 SQL library.** The course's Finance problem set uses `cs50.SQL`, which is a great teaching tool, but it's an extra dependency that only works neatly inside the CS50 codespace. Since the final project is explicitly meant to be runnable outside that environment, I used Python's standard library instead — it requires nothing beyond `pip install flask`, and keeps the project portable.

**One `subscriptions` table instead of separate tables per category or per status.** A subscription's category is just a text label, and "canceled" subscriptions are deleted rather than archived. I considered keeping a permanent history table (so canceled subscriptions could be reviewed later), but decided against it: this app's job is to answer "what am I paying for right now," not to be a financial ledger. Keeping the schema to one table made the rest of the logic — and the SQL itself — much easier to reason about.

**Signed cookie sessions instead of filesystem sessions.** Flask can store session data in a file on disk (which is what Finance's distribution code does, via `flask_session`) or in a small signed cookie in the browser, which is Flask's own default. I went with the simpler built-in option here, since it removes a dependency and a folder of session files that would otherwise need to be created and cleaned up.

**A "due soon" window of 7 days.** This number is hardcoded rather than configurable, on purpose — for a v1 of a personal tool, one sensible default beats an extra settings page that most users would never touch.

## AI assistance disclosure

I used Claude (Anthropic) while building this project, to help draft code, troubleshoot issues, and talk through design decisions, as explicitly permitted by CS50's final project policy. I reviewed, tested, and understood every part of the resulting code myself — the feature scope and the choices described above are mine.

## What I'd build next

Given more time, the natural next features would be: a simple chart showing spending by category, an option to pause a subscription instead of deleting it outright, and email or browser notifications a few days before a renewal — rather than only seeing the "due soon" badge when actually visiting the dashboard.
