import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_LOG_PATH = os.path.join(PROJECT_ROOT, "research_agent.log")

def setup_logger(log_file=DEFAULT_LOG_PATH):
    """
    Sets up a logger that outputs to both the console and a file in project root.
    """
    logger = logging.getLogger("T2MAgent")
    
    # Avoid adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Formatter for the log messages
        formatter = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler (append mode with proper error handling)
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create log file {log_file}: {e}")
            
    return logger

# Create a global logger instance
logger = setup_logger()
