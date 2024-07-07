from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import openai
from config import config

db = SQLAlchemy()
migrate = Migrate()
app_initialized = False

def create_app(config_name='default'):
    global app_initialized
    app = Flask(__name__)

    app.config.from_object(config[config_name])
    openai.api_key = app.config['OPENAI_API_KEY']

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from . import routes
        from .models import SessionData 
        app.register_blueprint(routes.main)
        db.create_all()

    app_initialized = True
    return app