"""
Subscription Manager — CS50x final project.

a small flask + sqlite web app for keeping track of recurring
subscriptions: what you're paying for, how much, how often, and
when it bills you next.

AI assistance disclosure: i used Claude (Anthropic) to help draft
and review this code while building my final project, as permitted
by the CS50 final project policy. the feature set, structure, and
the decisions behind them are mine — see README.md for a full
explanation of what i built and why.
"""

import sqlite3
from datetime import date, timedelta

from flask import Flask, flash, g, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, monthly_equivalent

app = Flask(__name__)

# signs the session cookie. fine for a school project; in a real
# deployment this would come from an environment variable instead.
app.secret_key = "please-change-this-secret-key"

DATABASE = "subscriptions.db"

CATEGORIES = [
    "Streaming",
    "Software",
    "Gaming",
    "Music",
    "Cloud / Hosting",
    "Fitness",
    "News",
    "Other",
]


def get_db():
    """open one database connection per request, and reuse it if called again"""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """close the connection once the request is done, so nothing leaks"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """create the tables on first run, so there's no manual setup step"""
    db = sqlite3.connect(DATABASE)

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            hash TEXT NOT NULL
        )
        """
    )
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (username)")

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            cost REAL NOT NULL,
            billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('monthly', 'yearly')),
            next_renewal TEXT NOT NULL,
            notes TEXT
        )
        """
    )
    db.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions (user_id)")

    db.commit()
    db.close()


init_db()


@app.route("/")
@login_required
def index():
    """the dashboard: every subscription you're tracking, plus the totals that matter"""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY next_renewal ASC",
        (session["user_id"],),
    ).fetchall()

    today = date.today()
    due_soon_cutoff = today + timedelta(days=7)

    subscriptions = []
    monthly_total = 0.0

    for row in rows:
        sub = dict(row)
        sub["due_soon"] = date.fromisoformat(sub["next_renewal"]) <= due_soon_cutoff
        subscriptions.append(sub)
        monthly_total += monthly_equivalent(sub["cost"], sub["billing_cycle"])

    return render_template(
        "index.html",
        subscriptions=subscriptions,
        monthly_total=monthly_total,
        yearly_total=monthly_total * 12,
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """add a new subscription to track"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        cost = request.form.get("cost", "")
        billing_cycle = request.form.get("billing_cycle", "")
        next_renewal = request.form.get("next_renewal", "")
        notes = request.form.get("notes", "").strip()

        if not name:
            return apology("give the subscription a name")
        if category not in CATEGORIES:
            return apology("pick a valid category")

        try:
            cost = float(cost)
            if cost <= 0:
                raise ValueError
        except ValueError:
            return apology("cost has to be a positive number")

        if billing_cycle not in ("monthly", "yearly"):
            return apology("billing cycle has to be monthly or yearly")

        try:
            date.fromisoformat(next_renewal)
        except ValueError:
            return apology("that renewal date doesn't look right")

        db = get_db()
        db.execute(
            """
            INSERT INTO subscriptions (user_id, name, category, cost, billing_cycle, next_renewal, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (session["user_id"], name, category, cost, billing_cycle, next_renewal, notes),
        )
        db.commit()

        flash(f"added {name}")
        return redirect("/")

    return render_template("add.html", categories=CATEGORIES, today=date.today().isoformat())


@app.route("/edit/<int:subscription_id>", methods=["GET", "POST"])
@login_required
def edit(subscription_id):
    """edit a subscription, but only if it actually belongs to whoever's logged in"""
    db = get_db()
    sub = db.execute(
        "SELECT * FROM subscriptions WHERE id = ? AND user_id = ?",
        (subscription_id, session["user_id"]),
    ).fetchone()

    if sub is None:
        return apology("that subscription doesn't exist", 404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        cost = request.form.get("cost", "")
        billing_cycle = request.form.get("billing_cycle", "")
        next_renewal = request.form.get("next_renewal", "")
        notes = request.form.get("notes", "").strip()

        if not name:
            return apology("give the subscription a name")
        if category not in CATEGORIES:
            return apology("pick a valid category")

        try:
            cost = float(cost)
            if cost <= 0:
                raise ValueError
        except ValueError:
            return apology("cost has to be a positive number")

        if billing_cycle not in ("monthly", "yearly"):
            return apology("billing cycle has to be monthly or yearly")

        try:
            date.fromisoformat(next_renewal)
        except ValueError:
            return apology("that renewal date doesn't look right")

        db.execute(
            """
            UPDATE subscriptions
            SET name = ?, category = ?, cost = ?, billing_cycle = ?, next_renewal = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (name, category, cost, billing_cycle, next_renewal, notes, subscription_id, session["user_id"]),
        )
        db.commit()

        flash(f"updated {name}")
        return redirect("/")

    return render_template("edit.html", sub=sub, categories=CATEGORIES)


@app.route("/delete/<int:subscription_id>", methods=["POST"])
@login_required
def delete(subscription_id):
    """cancel a subscription — removes it from the tracker for good"""
    db = get_db()
    db.execute(
        "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
        (subscription_id, session["user_id"]),
    )
    db.commit()

    flash("subscription removed")
    return redirect("/")


@app.route("/renew/<int:subscription_id>", methods=["POST"])
@login_required
def renew(subscription_id):
    """mark a subscription as just renewed, pushing its next bill date forward one cycle"""
    db = get_db()
    sub = db.execute(
        "SELECT * FROM subscriptions WHERE id = ? AND user_id = ?",
        (subscription_id, session["user_id"]),
    ).fetchone()

    if sub is None:
        return apology("that subscription doesn't exist", 404)

    current = date.fromisoformat(sub["next_renewal"])

    if sub["billing_cycle"] == "monthly":
        # python's date type has no built-in "add one month", so we handle
        # the year rollover by hand when the current month is december
        if current.month == 12:
            new_date = current.replace(year=current.year + 1, month=1)
        else:
            new_date = current.replace(month=current.month + 1)
    else:
        new_date = current.replace(year=current.year + 1)

    db.execute(
        "UPDATE subscriptions SET next_renewal = ? WHERE id = ? AND user_id = ?",
        (new_date.isoformat(), subscription_id, session["user_id"]),
    )
    db.commit()

    flash(f"{sub['name']} renewed — next bill on {new_date.isoformat()}")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """create a new account"""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        if not username:
            return apology("must provide username")
        if not password:
            return apology("must provide password")
        if password != confirmation:
            return apology("passwords don't match")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing is not None:
            return apology("that username is already taken")

        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()

        user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        session["user_id"] = user["id"]
        session["username"] = username

        flash("welcome! your account is ready")
        return redirect("/")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """log an existing user in"""
    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not username:
            return apology("must provide username")
        if not password:
            return apology("must provide password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None or not check_password_hash(user["hash"], password):
            return apology("invalid username and/or password")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """log the current user out"""
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
