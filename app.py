from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Static folder configuration
app.static_folder = 'static'
app.static_url_path = '/static'

# Ensure static directory exists
os.makedirs(app.static_folder, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'js'), exist_ok=True)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy()

def check_db_connection():
    """Check database connection and reconnect if necessary"""
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        try:
            db.session.rollback()
            db.session.remove()
            return False
        except:
            return False

@app.before_request
def before_request():
    """Ensure database connection before each request"""
    if not check_db_connection():
        db.session.remove()
        db.engine.dispose()

# Initialize app context and database
try:
    db.init_app(app)
    with app.app_context():
        import models
        import routes
        db.create_all()
        logger.info("Database initialization successful")
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    raise
