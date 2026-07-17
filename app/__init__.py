"""(The Setup) — This tells Python that app is a module and configures your database connection."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

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

# Your existing setup...
app.config['SECRET_KEY'] = 'your-very-secret-key' # You should already have this!

# Mail Configuration (Use Gmail SMTP for the MVP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# NEVER hardcode passwords! Use environment variables (.env)
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') 
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS') # This must be a Gmail "App Password", not your normal login!

mail = Mail(app)

# We import routes at the bottom to avoid circular dependencies
from app import routes, models