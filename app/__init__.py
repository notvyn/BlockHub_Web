"""(The Setup) — This tells Python that app is a module and configures your database connection."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

import cloudinary
import os
from dotenv import load_dotenv


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

# This command looks for the .env file and loads its contents into memory
load_dotenv()

# Now we pull the hidden variables using os.getenv()
cloudinary.config(
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
  api_key = os.getenv("CLOUDINARY_API_KEY"),
  api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

# We import routes at the bottom to avoid circular dependencies
from app import routes, models