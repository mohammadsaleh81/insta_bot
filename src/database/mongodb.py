import logging
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from ..config.settings import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.analysis_collection = None
        self.blocked_users_collection = None
        self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(MONGO_URI)
            self.db = self.client[DB_NAME]
            self.users_collection = self.db["users"]
            self.analysis_collection = self.db["analysis"]
            self.blocked_users_collection = self.db["blocked_users"]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            self.users_collection.create_index([("user_id", 1)], unique=True)
            self.users_collection.create_index([("role", 1)])
            self.analysis_collection.create_index([("user_id", 1)])
            self.analysis_collection.create_index([("created_at", -1)])
            self.blocked_users_collection.create_index([("user_id", 1)], unique=True)
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    async def save_user(self, user_id, first_name, last_name=None, username=None, lang_code=None, role="user"):
        """Save or update user information"""
        try:
            user_data = {
                "user_id": str(user_id),
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "lang_code": lang_code,
                "role": role,
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

    # Admin-specific methods
    async def get_all_users(self, skip=0, limit=50):
        """Get list of all users with pagination"""
        try:
            cursor = self.users_collection.find(
                {},
                {
                    "user_id": 1,
                    "first_name": 1,
                    "last_name": 1,
                    "username": 1,
                    "role": 1,
                    "coins": 1,
                    "analysis_count": 1,
                    "last_activity": 1
                }
            ).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return []

    async def get_user_analytics(self, user_id):
        """Get detailed analytics for a specific user"""
        try:
            user = self.users_collection.find_one({"user_id": str(user_id)})
            if not user:
                return None

            analysis_count = self.analysis_collection.count_documents({"user_id": str(user_id)})
            recent_analyses = list(self.analysis_collection.find(
                {"user_id": str(user_id)}
            ).sort("created_at", -1).limit(10))

            return {
                "user_info": user,
                "total_analyses": analysis_count,
                "recent_analyses": recent_analyses,
                "coins_balance": user.get("coins", 0),
                "last_activity": user.get("last_activity")
            }
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return None

    async def get_system_analytics(self):
        """Get system-wide analytics"""
        try:
            total_users = self.users_collection.count_documents({})
            total_analyses = self.analysis_collection.count_documents({})
            active_users_24h = self.users_collection.count_documents({
                "last_activity": {"$gte": datetime.now() - timedelta(hours=24)}
            })
            
            recent_analyses = list(self.analysis_collection.find().sort("created_at", -1).limit(10))
            
            return {
                "total_users": total_users,
                "total_analyses": total_analyses,
                "active_users_24h": active_users_24h,
                "recent_analyses": recent_analyses
            }
        except Exception as e:
            logger.error(f"Error getting system analytics: {str(e)}")
            return None

    async def block_user(self, user_id, reason=None):
        """Block a user"""
        try:
            self.blocked_users_collection.update_one(
                {"user_id": str(user_id)},
                {
                    "$set": {
                        "blocked_at": datetime.now(),
                        "reason": reason
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error blocking user: {str(e)}")
            return False

    async def unblock_user(self, user_id):
        """Unblock a user"""
        try:
            result = self.blocked_users_collection.delete_one({"user_id": str(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error unblocking user: {str(e)}")
            return False

    async def is_user_blocked(self, user_id):
        """Check if a user is blocked"""
        try:
            blocked = self.blocked_users_collection.find_one({"user_id": str(user_id)})
            return bool(blocked)
        except Exception as e:
            logger.error(f"Error checking if user is blocked: {str(e)}")
            return False

    async def get_user_full_history(self, user_id, skip=0, limit=100):
        """Get complete analysis history for a user"""
        try:
            cursor = self.analysis_collection.find(
                {"user_id": str(user_id)}
            ).sort("created_at", -1).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Error getting user full history: {str(e)}")
            return []

# Create global database instance
db = MongoDB() 