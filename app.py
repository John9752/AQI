import sys
import os
import logging

# Set up logging to stdout for Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing root app.py proxy...")
try:
    # Add backend directory to sys.path
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_path)
    logger.info(f"Added {backend_path} to sys.path")

    from app import app
    logger.info("Successfully imported app from backend.app")
except Exception as e:
    logger.error(f"FAILED to initialize app: {str(e)}")
    raise e

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8888))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
