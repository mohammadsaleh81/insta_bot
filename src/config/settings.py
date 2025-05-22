import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Telegram API Settings
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')

# Coin Settings
ANALYSIS_COST = 10  # Cost per analysis
CHAT_COST = 2      # Cost per chat message
DEFAULT_COINS = 100  # Default free coins for new users

# MongoDB Settings
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "insta_analyzer_db"

# OpenAI Settings
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# File Storage Settings
HISTORY_DIR = "user_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Logging Settings
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Create log filename with current date
LOG_FILENAME = os.path.join(LOG_DIR, f"insta_bot_{datetime.now().strftime('%Y-%m-%d')}.log")

# Logging format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        # File handler for saving logs to file
        logging.FileHandler(LOG_FILENAME, encoding='utf-8'),
        # Stream handler for console output
        logging.StreamHandler()
    ]
)

# Logging Settings
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO' 