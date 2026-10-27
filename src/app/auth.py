import functools
import logging
import random

import bcrypt
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .db import get_db

bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if user is not None and bcrypt.checkpw(password.encode(), user["password_hash"]):
            session.clear()
            session["user_id"] = user["id"]
            logger.info("Login succeeded for %s", username)
            return redirect(url_for("notes.index"))
        logger.warning("Login failed for %s", username)
        flash("Invalid username or password.")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        username = request.form.get("username", "")
        token = str(random.randint(100000, 999999))
        db = get_db()
        db.execute("UPDATE users SET reset_token = ? WHERE username = ?", (token, username))
        db.commit()
        # TODO: email the link to the user; logged for now
        logger.info("Password reset link for %s: /reset/%s", username, token)
        flash("If the account exists, a reset link has been sent.")
    return render_template("forgot.html")


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE reset_token = ?", (token,)).fetchone()
    if user is None:
        flash("Invalid reset link.")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        password_hash = bcrypt.hashpw(request.form["password"].encode(), bcrypt.gensalt())
        db.execute(
            "UPDATE users SET password_hash = ?, reset_token = NULL WHERE id = ?",
            (password_hash, user["id"]),
        )
        db.commit()
        flash("Password updated. Please log in.")
        return redirect(url_for("auth.login"))
    return render_template("reset.html")
