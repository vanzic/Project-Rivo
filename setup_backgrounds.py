import logging
import sys
import os

# Add project root to path so we can import app modules
sys.path.append(os.getcwd())

from app.managers.background_manager import BackgroundManager

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("BackgroundSetup")

def generate_backgrounds():
    logger.info("Initializing Background Manager...")
    manager = BackgroundManager()
    
    logger.info("Ensuring all background assets exist...")
    manager.ensure_all_assets()
    
    logger.info("Background setup complete.")

if __name__ == "__main__":
    generate_backgrounds()
