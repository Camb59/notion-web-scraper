import os
import sys
import logging
from app import app, db
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('main_app.log')
    ]
)
logger = logging.getLogger(__name__)

def verify_database():
    """Verify database connection and schema"""
    with app.app_context():
        try:
            # Basic connection test
            db.session.execute(text('SELECT 1'))
            logger.info("Basic database connection successful")
            
            # Check if all required tables exist
            tables = db.session.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )).fetchall()
            
            table_names = [table[0] for table in tables]
            logger.info(f"Found tables: {', '.join(table_names)}")
            
            # Verify specific tables
            required_tables = {'scraped_content'}
            missing_tables = required_tables - set(table_names)
            
            if missing_tables:
                logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                logger.info("Creating missing tables...")
                db.create_all()
            else:
                logger.info("All required tables exist")
            
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise

def verify_port(port):
    """Verify if the port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except socket.error:
        logger.error(f"Port {port} is already in use")
        return False

if __name__ == "__main__":
    try:
        # Environment setup verification
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        port = int(os.environ.get('PORT', 5000))
        
        logger.info("Starting application verification...")
        logger.info(f"Debug mode: {debug_mode}")
        logger.info(f"Port: {port}")
        
        # Verify database connection
        if not verify_database():
            raise Exception("Database verification failed")
        
        # Verify port availability
        if not verify_port(port):
            raise Exception(f"Port {port} is not available")
        
        # Start the application
        logger.info("Starting Flask application...")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=False
        )
        
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        logger.error("Please check your database connection and environment variables")
        sys.exit(1)
