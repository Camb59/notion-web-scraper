from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging
import os
import sys
import traceback
import socket

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Debug mode configuration
app.debug = os.environ.get('FLASK_ENV') == 'development'

# Static folder configuration
app.static_folder = 'static'
app.static_url_path = '/static'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 if app.debug else 31536000

# Ensure static directory exists
os.makedirs(app.static_folder, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'js'), exist_ok=True)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev_key')

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    logger.error("DATABASE_URL is not set")
    raise ValueError("DATABASE_URL environment variable is required")

if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'pool_size': 10,
    'max_overflow': 5
}

# Initialize database
from models import db
db.init_app(app)

# Import routes after app initialization
with app.app_context():
    from routes import register_routes
    register_routes(app)
    
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        logger.info('Database connection successful')
        
        # Create database tables
        db.create_all()
        logger.info('Database tables created successfully')
    except Exception as e:
        logger.error(f'Error during database setup: {str(e)}')
        raise

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('0.0.0.0', port))
                logger.info(f'Found available port: {port}')
                return port
        except socket.error:
            logger.warning(f'Port {port} is already in use')
            continue
    
    # If no port is found, try a random port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('0.0.0.0', 0))
        port = sock.getsockname()[1]
        logger.info(f'Using random port: {port}')
        return port

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f'Attempting to start Flask application on port {port}...')
        
        # Check if the specified port is available
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('0.0.0.0', port))
        except socket.error:
            logger.warning(f'Port {port} is already in use, finding another port...')
            port = find_available_port(start_port=port)
        
        logger.info(f'Starting Flask application on port {port}...')
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f'Application failed to start: {str(e)}')
        logger.error(f'Exception details: {traceback.format_exc()}')
        raise
