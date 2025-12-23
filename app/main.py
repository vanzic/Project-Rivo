import sys
import time
import signal
import logging
import json
import json
import uuid
import threading
from app.config import load_config
from app.services.trend_poller import TrendPoller
from app.sources.mock_source import MockTrendSource
from app.sources.rss_source import RSSSource

# Global flag for shutdown
SHUTDOWN_EVENT = threading.Event()

class CorrelationIdFilter(logging.Filter):
    """Injects correlation ID into logs."""
    def __init__(self, correlation_id):
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record):
        record.correlation_id = self.correlation_id
        return True

def setup_logging(correlation_id):
    """Configures structured logging with correlation ID."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if re-called (though safe here)
    if logger.handlers:
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(correlation_id)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter(correlation_id))
    logger.addHandler(handler)

def shutdown_handler(signum, frame):
    """Handles graceful shutdown signals."""
    logging.info("Shutdown signal received")
    logging.info("System stopping")
    SHUTDOWN_EVENT.set()

def main():
    """Main entry point for the application."""
    # Generate correlation ID at startup
    correlation_id = str(uuid.uuid4())
    setup_logging(correlation_id)
    
    # Load and log configuration
    config = load_config()
    # Filter out potential secrets for logging safety if needed, 
    # but for minimal bootstrap we just log safe keys or all if no secrets known.
    # We will simply log that config is loaded and maybe a few keys or the whole dict if small.
    # "log the resolved configuration (safe values only)"
    # For now, we'll log keys.
    safe_config = {k: v for k, v in config.items() if 'KEY' not in k.upper() and 'SECRET' not in k.upper() and 'PASSWORD' not in k.upper()}
    logging.info(f"Configuration loaded: {json.dumps(safe_config)}")
    
    logging.info("System starting...")

    # precise single entry point side effects
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logging.info(f"Configuration loaded: {json.dumps(safe_config)}")
    
    # Initialize and start services
    # Initialize and start services
    mock_source = MockTrendSource()
    # RSS Source (Hacker News)
    rss_source = RSSSource("https://news.ycombinator.com/rss", name="HackerNews")
    
    trend_poller = TrendPoller(sources=[mock_source, rss_source], interval=30)
    trend_poller.start()

    logging.info("System initialized. Running main loop.")

    last_heartbeat = time.time()

    try:
        while not SHUTDOWN_EVENT.is_set():
            start_time = time.time()
            
            # Simulate application work
            # Use wait instead of sleep to respond to shutdown faster
            if SHUTDOWN_EVENT.wait(1):
                break
            
            # Heartbeat logic
            current_time = time.time()
            if current_time - last_heartbeat >= 10:
                logging.info("Heartbeat")
                last_heartbeat = current_time
            
            end_time = time.time()
            logging.info(f"Loop execution time: {end_time - start_time:.4f}s")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        # Ensure cleanup even on error
    finally:
        # Cleanup
        trend_poller.stop()
        logging.info("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
