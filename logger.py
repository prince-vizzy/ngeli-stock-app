# logging_config.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(app):
    # Create logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Rotating file handler (keeps logs manageable)
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=5_000_000, backupCount=5)
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    file_handler.setFormatter(formatter)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Optional: also log to console in dev
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)
