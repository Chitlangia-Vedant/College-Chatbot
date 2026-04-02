import logging
import sys

def setup_logger(name: str):
    logger = logging.getLogger(name)
    
    # Prevent duplicate logs if the logger is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Structured format: Timestamp - [Level] - Module - Message
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
        )
        
        # 1. Print logs to the terminal
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. Save logs to a file
        file_handler = logging.FileHandler("chatbot_backend.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger