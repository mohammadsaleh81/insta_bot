import logging
from ..database.mongodb import db
from ..config.settings import DEFAULT_COINS

logger = logging.getLogger(__name__)

class CoinService:
    async def get_user_coins(self, user_id):
        """Get user's coin balance"""
        return await db.get_user_coins(user_id)

    async def update_user_coins(self, user_id, coins):
        """Update user's coin balance"""
        return await db.update_user_coins(user_id, coins)

    async def add_coins(self, user_id, amount):
        """Add coins to user's balance"""
        current_coins = await self.get_user_coins(user_id)
        new_coins = current_coins + amount
        success = await self.update_user_coins(user_id, new_coins)
        return success, new_coins

    async def deduct_coins(self, user_id, amount):
        """Deduct coins from user's balance"""
        current_coins = await self.get_user_coins(user_id)
        if current_coins >= amount:
            new_coins = current_coins - amount
            success = await self.update_user_coins(user_id, new_coins)
            return success, new_coins
        return False, current_coins

    async def initialize_user_coins(self, user_id):
        """Initialize new user with default coins"""
        success = await self.update_user_coins(user_id, DEFAULT_COINS)
        return success, DEFAULT_COINS

# Create global coin service instance
coin_service = CoinService() 