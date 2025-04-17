from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from handicap.config import Config
  
# Needed to create a db.
class Base(DeclarativeBase):
    pass
# Create the database.
db = SQLAlchemy(model_class=Base)

# Initialise the app with all of the extensions.
#db.init_app()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'        # The html template displayed when the login_required requires login.
login_manager.login_message_category = 'info'   # Blue backround on the alert message.

mail = Mail()

def create_app(config_class=Config):
    """Create a Flask application."""
    # Create the app.
    app = Flask(__name__)
    app.config.from_object(config_class)  # Load the config from the config.py file.

    db.init_app(app)  # Initialise the database with the app.
    bcrypt.init_app(app)    # Initialise the bcrypt with the app.
    login_manager.init_app(app)  # Initialise the login manager with the app.
    mail.init_app(app)  # Initialise the mail with the app.

    # Register the blueprints.
    from handicap.users.routes import users
    from handicap.scores.routes import scores
    from handicap.main.routes import main
    from handicap.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(scores)
    app.register_blueprint(main)
    app.register_blueprint(errors)  # Register the errors blueprint.

    with app.app_context():
        db.create_all()

    return app