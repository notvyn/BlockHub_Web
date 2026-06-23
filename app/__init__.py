"""(The Setup) — This tells Python that app is a module and configures your database connection."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Create the App
app = Flask(__name__)

# Configure the App
app.config['SECRET_KEY'] = 'a_super_secret_key_you_will_change_later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blockhub.db'

# Plug in the Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Plug in the LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# We import routes at the bottom to avoid circular dependencies
from app import routes, models