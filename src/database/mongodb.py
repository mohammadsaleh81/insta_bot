import logging
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from ..config.settings import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.analysis_collection = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.users_collection = self.db["users"]
            self.analysis_collection = self.db["analysis"]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            self.users_collection.create_index([("user_id", 1)], unique=True)
            self.analysis_collection.create_index([("user_id", 1)])
            self.analysis_collection.create_index([("created_at", -1)])
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    async def save_user(self, user_id, first_name, last_name=None, username=None, lang_code=None):
        """Save or update user information"""
        try:
            user_data = {
                "user_id": str(user_id),
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "lang_code": lang_code,
                "last_activity": datetime.now()
            }
            
            self.users_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": user_data},
                upsert=True
            )
            logger.info(f"User {user_id} information updated in database")
            
        except Exception as e:
            logger.error(f"Error saving user information: {str(e)}")
            raise

    async def save_analysis(self, user_id, username, analysis):
        """Save analysis to database"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            analysis_doc = {
                "user_id": str(user_id),
                "username": username,
                "timestamp": timestamp,
                "analysis": analysis,
                "created_at": datetime.now()
            }
            
            self.analysis_collection.insert_one(analysis_doc)
            logger.info(f"Analysis for {username} saved to database")
            
            # Update user's analysis count
            self.users_collection.update_one(
                {"user_id": str(user_id)},
                {"$inc": {"analysis_count": 1}, "$set": {"last_activity": datetime.now()}},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            return False

    async def get_user_coins(self, user_id):
        """Get user's coin balance"""
        try:
            user_doc = self.users_collection.find_one({"user_id": str(user_id)})
            return user_doc.get("coins", 0) if user_doc else 0
        except Exception as e:
            logger.error(f"Error getting user coins: {str(e)}")
            return 0

    async def update_user_coins(self, user_id, coins):
        """Update user's coin balance"""
        try:
            self.users_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {"coins": coins}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating user coins: {str(e)}")
            return False

    async def get_user_history(self, user_id, limit=10):
        """Get user's analysis history"""
        try:
            cursor = self.analysis_collection.find(
                {"user_id": str(user_id)},
                {"username": 1, "timestamp": 1, "analysis": {"$substr": ["$analysis", 0, 100]}}
            ).sort("created_at", -1).limit(limit)
            
            return list(cursor)
            
        except Exception as e:
            logger.error(f"Error getting user history: {str(e)}")
            return []

# Create global database instance
db = MongoDB() 