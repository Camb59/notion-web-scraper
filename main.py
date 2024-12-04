import os
import logging
from app import app

if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    logging.basicConfig(level=logging.INFO)
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logging.error(f"Application failed to start: {str(e)}")
        raise
