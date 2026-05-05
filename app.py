from flask import Flask
from config import Config
from extensions import db, login_manager, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = "auth.login"

    from models.user import User
    from models.event import Event
    from models.search import Search

    from routes.auth import auth_bp
    from routes.events import events_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

        from services.data_loader import load_events_to_database
        load_events_to_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
