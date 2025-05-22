from datetime import datetime
from models.user import User, States
from pymongo import MongoClient
import logging
import os

logger = logging.getLogger(__name__)

class UserManager:
    """Manager for user states, profiles, and interactions"""
    
    def __init__(self, mongo_client, db_name="insta_analyzer_db"):
        self.mongo_client = mongo_client
        self.db = mongo_client[db_name]
        self.users_collection = self.db["users"]
        self.analysis_collection = self.db["analysis"]
        
        # Cache for user states and data
        self.user_states = {}
        self.user_profile_info = {}
        self.user_history = {}
        self.user_chat_history = {}
        
        # Constants
        self.DEFAULT_COINS = 100  # سکه‌های رایگان اولیه برای کاربران جدید
        self.ANALYSIS_COST = 10   # هزینه هر تحلیل
        self.CHAT_COST = 2        # هزینه هر پیام چت
        
        # References to States enum from models.user
        self.States = States
    
    # ------------------- User State Methods -------------------
    
    def get_user_state(self, user_id):
        """Get current state for a user"""
        user_id = str(user_id)
        if user_id not in self.user_states:
            self.user_states[user_id] = self.States.MAIN_MENU
        return self.user_states[user_id]
    
    def set_user_state(self, user_id, state):
        """Set state for a user"""
        user_id = str(user_id)
        self.user_states[user_id] = state
    
    # ------------------- User Profile Methods -------------------
    
    def clear_profile_info(self, user_id):
        """Clear temporary profile info for a user"""
        user_id = str(user_id)
        if user_id in self.user_profile_info:
            del self.user_profile_info[user_id]
    
    def get_profile_info(self, user_id):
        """Get temporary profile info for a user"""
        user_id = str(user_id)
        return self.user_profile_info.get(user_id, {})
    
    def set_profile_info(self, user_id, key, value):
        """Set a profile info value for a user"""
        user_id = str(user_id)
        if user_id not in self.user_profile_info:
            self.user_profile_info[user_id] = {}
        self.user_profile_info[user_id][key] = value
    
    # ------------------- Database Methods -------------------
    
    async def save_user(self, user_id, first_name, last_name=None, username=None, lang_code=None):
        """Save or update user in database"""
        user_id_str = str(user_id)
        
        user_data = {
            "user_id": user_id_str,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "lang_code": lang_code,
            "last_activity": datetime.now()
        }
        
        try:
            self.users_collection.update_one(
                {"user_id": user_id_str},
                {"$set": user_data},
                upsert=True
            )
            logger.info(f"اطلاعات کاربر {user_id_str} در پایگاه داده بروزرسانی شد")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره‌سازی اطلاعات کاربر: {str(e)}")
            return False
    
    async def get_user_info(self, user_id):
        """Get user info from database"""
        user_id_str = str(user_id)
        
        try:
            user_doc = self.users_collection.find_one({"user_id": user_id_str})
            if user_doc:
                return {
                    "user_id": user_doc.get("user_id", ""),
                    "first_name": user_doc.get("first_name", ""),
                    "last_name": user_doc.get("last_name", ""),
                    "username": user_doc.get("username", ""),
                    "coins": user_doc.get("coins", 0),
                    "analysis_count": user_doc.get("analysis_count", 0),
                    "join_date": user_doc.get("created_at", datetime.now()).strftime("%Y-%m-%d"),
                    "last_activity": user_doc.get("last_activity", datetime.now()).strftime("%Y-%m-%d %H:%M")
                }
            return None
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات کاربر: {str(e)}")
            return None
    
    # ------------------- Coin Management Methods -------------------
    
    async def get_user_coins(self, user_id):
        """Get user's coin balance"""
        user_id_str = str(user_id)
        
        try:
            user_doc = self.users_collection.find_one({"user_id": user_id_str})
            if user_doc:
                return user_doc.get("coins", 0)
            return 0
        except Exception as e:
            logger.error(f"خطا در دریافت سکه‌های کاربر: {str(e)}")
            return 0
    
    async def update_user_coins(self, user_id, coins):
        """Update user's coin balance"""
        user_id_str = str(user_id)
        
        try:
            self.users_collection.update_one(
                {"user_id": user_id_str},
                {"$set": {"coins": coins}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"خطا در بروزرسانی سکه‌های کاربر: {str(e)}")
            return False
    
    async def add_coins(self, user_id, amount):
        """Add coins to user's balance"""
        user_id_str = str(user_id)
        current_coins = await self.get_user_coins(user_id_str)
        new_coins = current_coins + amount
        success = await self.update_user_coins(user_id_str, new_coins)
        return success, new_coins
    
    async def deduct_coins(self, user_id, amount):
        """Deduct coins from user's balance"""
        user_id_str = str(user_id)
        current_coins = await self.get_user_coins(user_id_str)
        
        if current_coins >= amount:
            new_coins = current_coins - amount
            success = await self.update_user_coins(user_id_str, new_coins)
            return success, new_coins
        return False, current_coins
    
    # ------------------- Analysis History Methods -------------------
    
    async def save_analysis(self, user_id, username, analysis):
        """Save analysis to history and database"""
        user_id_str = str(user_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to cache
        if user_id_str not in self.user_history:
            self.user_history[user_id_str] = []
        
        analysis_data = {
            "timestamp": timestamp,
            "username": username,
            "analysis": analysis[:100] + "..."  # Save summary
        }
        
        self.user_history[user_id_str].insert(0, analysis_data)
        self.user_history[user_id_str] = self.user_history[user_id_str][:10]  # Keep only 10 most recent
        
        # Save to database
        try:
            analysis_document = {
                "user_id": user_id_str,
                "username": username,
                "timestamp": timestamp,
                "analysis": analysis,
                "created_at": datetime.now()
            }
            
            self.analysis_collection.insert_one(analysis_document)
            logger.info(f"تحلیل برای {username} در پایگاه داده ذخیره شد")
            
            # Update user stats
            self.users_collection.update_one(
                {"user_id": user_id_str},
                {"$inc": {"analysis_count": 1}, "$set": {"last_activity": datetime.now()}},
                upsert=True
            )
            
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره‌سازی تحلیل در پایگاه داده: {str(e)}")
            return False
    
    async def get_user_history(self, user_id, limit=10):
        """Get user's analysis history"""
        user_id_str = str(user_id)
        
        if user_id_str in self.user_history:
            return self.user_history[user_id_str]
        
        try:
            cursor = self.analysis_collection.find(
                {"user_id": user_id_str},
                {"username": 1, "timestamp": 1, "analysis": {"$substr": ["$analysis", 0, 100]}}
            ).sort("created_at", -1).limit(limit)
            
            history_items = []
            for doc in cursor:
                history_items.append({
                    "timestamp": doc.get("timestamp", ""),
                    "username": doc.get("username", ""),
                    "analysis": doc.get("analysis", "") + "..."
                })
            
            self.user_history[user_id_str] = history_items
            return history_items
        except Exception as e:
            logger.error(f"خطا در بازیابی تاریخچه از پایگاه داده: {str(e)}")
            return [] 