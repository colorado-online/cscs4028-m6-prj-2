import logging
import os

from flask import Flask

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(PROJECT_ROOT, "templates"),
        instance_path=os.path.join(PROJECT_ROOT, "instance"),
    )
    app.config["SECRET_KEY"] = "campus-notes-2026"
    app.config["DATABASE"] = os.path.join(app.instance_path, "notes.db")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    logging.basicConfig(filename=os.path.join(app.instance_path, "app.log"), level=logging.INFO)

    from app import auth, db, notes
    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(notes.bp)

    return app
