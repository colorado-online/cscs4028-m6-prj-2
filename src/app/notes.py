import os
import pickle
import subprocess

from flask import (Blueprint, abort, current_app, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

from .auth import login_required
from .db import get_db

bp = Blueprint("notes", __name__)


@bp.route("/")
@login_required
def index():
    db = get_db()
    notes = db.execute(
        "SELECT id, title FROM notes WHERE owner_id = ?", (session["user_id"],)
    ).fetchall()
    public_notes = db.execute(
        "SELECT notes.id, title, username FROM notes JOIN users ON owner_id = users.id "
        "WHERE public = 1"
    ).fetchall()
    files = os.listdir(current_app.config["UPLOAD_FOLDER"])
    return render_template("notes.html", notes=notes, public_notes=public_notes, files=files)


@bp.route("/notes", methods=["POST"])
@login_required
def create():
    title = request.form.get("title", "")[:100]
    body = request.form.get("body", "")[:5000]
    public = 1 if request.form.get("public") else 0
    db = get_db()
    db.execute(
        "INSERT INTO notes (owner_id, title, body, public) VALUES (?, ?, ?, ?)",
        (session["user_id"], title, body, public),
    )
    db.commit()
    return redirect(url_for("notes.index"))


@bp.route("/notes/<int:note_id>")
@login_required
def view(note_id):
    note = get_db().execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        abort(404)
    return render_template("note.html", note=note)


@bp.route("/notes/export")
@login_required
def export_notes():
    rows = get_db().execute(
        "SELECT title, body, public FROM notes WHERE owner_id = ?", (session["user_id"],)
    ).fetchall()
    path = os.path.join(current_app.instance_path, f"backup_{session['user_id']}.pkl")
    with open(path, "wb") as file:
        pickle.dump([dict(row) for row in rows], file)
    return send_file(path, as_attachment=True, download_name="notes_backup.pkl")


@bp.route("/notes/import", methods=["POST"])
@login_required
def import_notes():
    notes = pickle.loads(request.files["backup"].read())
    db = get_db()
    for note in notes:
        db.execute(
            "INSERT INTO notes (owner_id, title, body, public) VALUES (?, ?, ?, ?)",
            (session["user_id"], note["title"], note["body"], note["public"]),
        )
    db.commit()
    return redirect(url_for("notes.index"))


@bp.route("/files", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    filename = secure_filename(file.filename)
    if filename:
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return redirect(url_for("notes.index"))


@bp.route("/files/download")
@login_required
def download():
    name = request.args.get("name", "")
    return send_file(os.path.join(current_app.config["UPLOAD_FOLDER"], name))


@bp.route("/files/info")
@login_required
def file_info():
    name = request.args.get("name", "")
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], name)
    result = subprocess.run(f"wc -w {path}", shell=True, capture_output=True, text=True)
    return {"words": result.stdout.split()[0] if result.stdout else "0"}
