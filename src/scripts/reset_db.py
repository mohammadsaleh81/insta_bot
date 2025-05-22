import sys
import os
import logging
from pymongo import MongoClient
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MONGO_URI, DB_NAME, LOG_FORMAT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(os.path.join('logs', f'db_reset_{datetime.now().strftime("%Y-%m-%d")}.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def reset_database():
    """Reset the MongoDB database by dropping all collections and recreating them with proper indexes"""
    try:
        # Connect to MongoDB
        logger.info(f"Connecting to MongoDB at {MONGO_URI}")
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # List of collections to reset
        collections = ['users', 'analysis']
        
        # Drop each collection
        for collection_name in collections:
            logger.info(f"Dropping collection: {collection_name}")
            db[collection_name].drop()
        
        # Recreate collections with indexes
        logger.info("Recreating collections with indexes...")
        
        # Users collection
        users_collection = db["users"]
        users_collection.create_index([("user_id", 1)], unique=True)
        logger.info("Created index on users collection: user_id (unique)")
        
        # Analysis collection
        analysis_collection = db["analysis"]
        analysis_collection.create_index([("user_id", 1)])
        analysis_collection.create_index([("created_at", -1)])
        logger.info("Created indexes on analysis collection: user_id, created_at")
        
        logger.info("Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    if reset_database():
        print("✅ Database reset completed successfully!")
    else:
        print("❌ Error resetting database. Check the logs for details.") 