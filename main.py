import os
import logging
from app import app, db

if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log environment status
    required_vars = ['DATABASE_URL', 'NOTION_TOKEN', 'NOTION_DATABASE_ID']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logging.info("All required environment variables are present")
    
    try:
        # Test database connection
        with app.app_context():
            db.session.execute('SELECT 1')
            logging.info("Database connection successful")
        
        # Run the Flask application
        app.run(host='0.0.0.0', port=5000, debug=debug_mode)
    except Exception as e:
        logging.error(f"Application failed to start: {str(e)}")
        logging.error("Please check your database connection and environment variables")
        raise
