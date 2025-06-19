import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_caching import Cache
import redis

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOST')
app.config['CACHE_REDIS_PORT'] = os.getenv('REDIS_PORT')
app.config['CACHE_REDIS_DB'] = os.getenv('REDIS_DB')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"

cache = Cache(app=app)
cache.init_app(app)

redis_client = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))

user_create_secret_key = os.getenv('USER_CREATE_SECRET_KEY')
xero_client_id = os.getenv('XERO_CLIENT_ID')
xero_client_secret = os.getenv('XERO_CLIENT_SECRET')
bukku_token = os.getenv('BUKKU_TOKEN')
bukku_subdomain = os.getenv('BUKKU_SUBDOMAIN')

from app import models, routes

app.register_blueprint(routes.api_bp)