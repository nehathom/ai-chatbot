import logging
from datetime import datetime
from pathlib import Path

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure logging with a simpler format to avoid % issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"rag_system_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

def get_logger(name: str):
    """Get a logger instance for a module."""
    return logging.getLogger(name)