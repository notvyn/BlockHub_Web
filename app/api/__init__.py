from flask import Blueprint

api = Blueprint('api', __name__) # automatically prepend '/api' to every single route

# url_prefix='/api'

from app.api import routes