from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
import cloudinary
import os
from dotenv import load_dotenv

# 1. Initialize extensions globally (BUT DO NOT attach the app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

# Load env variables
load_dotenv()

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    # Make sure to import User inside or at the top depending on your setup
    from app.models import User
    return User.query.get(int(user_id))

# 2. The Application Factory
def create_app():
    # Create the App
    app = Flask(__name__)

    # Configure the App
    app.config['SECRET_KEY'] = 'your-very-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blockhub.db'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

    # 3. Initialize the extensions WITH the app
    db.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Notice this changes to point to the auth blueprint!
    
    mail.init_app(app)

    # 4. Register your Blueprints here
    from app.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # 5. Return the fully built app
    return app