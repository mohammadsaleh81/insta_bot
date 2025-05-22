import logging
from telethon import TelegramClient
from config.settings import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    LOG_FORMAT,
    LOG_LEVEL
)
from handlers.button_handler import ButtonHandler
from handlers.message_handler import MessageHandler
from handlers.analysis_handler import AnalysisHandler

# Configure logging
logging.basicConfig(
    format=LOG_FORMAT,
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)

class UserManager:
    def __init__(self):
        self.users = {}
        self.analysis_handler = None

    def set_analysis_handler(self, handler):
        self.analysis_handler = handler

    def get_user(self, user_id):
        return self.users.get(user_id)

    def get_or_create_user(self, user_id, first_name):
        if user_id not in self.users:
            from models.user import User
            self.users[user_id] = User(user_id, first_name)
        return self.users[user_id]

class Bot:
    def __init__(self):
        self.client = TelegramClient(
            'insta_analyzer_bot',
            API_ID,
            API_HASH
        ).start(bot_token=BOT_TOKEN)

        self.user_manager = UserManager()
        
        # Initialize handlers
        self.analysis_handler = AnalysisHandler(self.client, self.user_manager)
        self.user_manager.set_analysis_handler(self.analysis_handler)
        
        self.button_handler = ButtonHandler(self.client, self.user_manager)
        self.message_handler = MessageHandler(self.client, self.user_manager)
        
        # Register handlers
        self.button_handler.register_handlers()
        self.message_handler.register_handlers()

    def run(self):
        """Start the bot"""
        logger.info("Bot started.")
        self.client.run_until_disconnected()

if __name__ == "__main__":
    bot = Bot()
    bot.run() 