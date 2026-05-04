import os
from flask import Flask
from config import Config
from app.extensions import mail


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)

    # ── Upload folder ─────────────────────────────────────
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'resumes')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # ── Init extensions ───────────────────────────────────
    mail.init_app(app)

    # ── Register Blueprints ───────────────────────────────
    from app.main.routes      import main_bp
    from app.auth.routes      import auth_bp
    from app.jobseeker.routes import jobseeker_bp
    from app.employer.routes  import employer_bp
    from app.admin.routes     import admin_bp
    from app.messages.routes  import messages_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobseeker_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(messages_bp)

    return app
