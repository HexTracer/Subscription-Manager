"""
helper functions for the subscription manager.

kept separate from app.py so the routes file stays focused on
"what happens when this url is hit" rather than utility logic.
"""

from functools import wraps

from flask import redirect, render_template, session


def login_required(f):
    """send a visitor to the login page if nobody's signed in yet"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """show a simple, friendly error page instead of a stack trace or a silent failure"""
    return render_template("apology.html", message=message), code


def monthly_equivalent(cost, billing_cycle):
    """
    convert any subscription's cost into a monthly figure.

    this is what lets a $9.99/month plan and a $99/year plan
    show up side by side in one honest total.
    """
    if billing_cycle == "yearly":
        return cost / 12
    return cost
