import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

def check_db_connection():
    """Check database connection and reconnect if necessary"""
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
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

with app.app_context():
    import models
    import routes
    db.create_all()
    # Initial database connection check
    check_db_connection()
