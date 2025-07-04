from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Set
from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

@dataclass
class UserProfile:
    username: str
    name: Optional[str] = None
    birth_year: Optional[int] = None
    age_estimate: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    job: Optional[str] = None
    notable_event: Optional[str] = None
    relationship: Optional[str] = None

class States:
    MAIN_MENU = 0
    TYPING_USERNAME = 1
    TYPING_NAME = 2
    TYPING_BIRTH_YEAR = 3
    TYPING_GENDER = 4
    TYPING_CITY = 5
    TYPING_JOB = 6
    TYPING_EVENT = 7
    TYPING_RELATIONSHIP = 8
    VIEWING_HISTORY = 9
    VIEWING_PROFILE = 10
    CHATTING_WITH_AI = 11
    SEARCHING = 12

class User:
    """User model class for storing user information"""
    
    def __init__(self, user_id, first_name, last_name=None, username=None, lang_code=None, role: UserRole = UserRole.USER):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.lang_code = lang_code
        self.coins = 0
        self.profile_info = {}
        self.role = role
        self.state = States.MAIN_MENU
        self.chat_history = []
        self.current_analysis = None
        
    def get_full_name(self):
        """Get user's full name"""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
        
    def update_coins(self, amount):
        """Update user's coin balance"""
        self.coins = amount
        
    def add_coins(self, amount):
        """Add coins to user's balance"""
        self.coins += amount
        
    def deduct_coins(self, amount):
        """Deduct coins from user's balance"""
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False
        
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN

    def to_dict(self):
        """Convert user to dictionary for database storage"""
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "lang_code": self.lang_code,
            "coins": self.coins,
            "role": self.role.value
        }

    def set_state(self, state: int) -> None:
        """Set user's current state"""
        self.state = state

    def get_state(self) -> int:
        """Get user's current state"""
        return self.state

    def set_profile_info(self, profile_info: UserProfile) -> None:
        """Set user's profile information"""
        self.profile_info = profile_info

    def get_profile_info(self) -> Optional[UserProfile]:
        """Get user's profile information"""
        return self.profile_info

    def add_chat_message(self, role: str, content: str) -> None:
        """Add a message to user's chat history"""
        self.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })

    def get_chat_history(self, limit: int = 20) -> List[Dict]:
        """Get user's chat history"""
        return self.chat_history[-limit:]

    def set_current_analysis(self, analysis: Dict) -> None:
        """Set user's current analysis"""
        self.current_analysis = analysis

    def get_current_analysis(self) -> Optional[Dict]:
        """Get user's current analysis"""
        return self.current_analysis 

class Admin(User):
    """Admin model class with extended privileges"""
    
    def __init__(self, user_id, first_name, last_name=None, username=None, lang_code=None):
        super().__init__(user_id, first_name, last_name, username, lang_code, role=UserRole.ADMIN)
        
    def get_all_users(self, db_connection) -> List[User]:
        """Get list of all users"""
        # This method will be implemented when connecting to the database
        pass
        
    def get_user_analytics(self, user_id: int, db_connection) -> Dict:
        """Get analytics for a specific user"""
        # This method will be implemented when connecting to the database
        pass
        
    def get_system_analytics(self, db_connection) -> Dict:
        """Get system-wide analytics"""
        # This method will be implemented when connecting to the database
        pass
        
    def block_user(self, user_id: int, db_connection) -> bool:
        """Block a user from using the bot"""
        # This method will be implemented when connecting to the database
        pass
        
    def unblock_user(self, user_id: int, db_connection) -> bool:
        """Unblock a user"""
        # This method will be implemented when connecting to the database
        pass
        
    def modify_user_coins(self, user_id: int, amount: int, db_connection) -> bool:
        """Modify a user's coin balance"""
        # This method will be implemented when connecting to the database
        pass
        
    def get_user_chat_history(self, user_id: int, db_connection, limit: int = 100) -> List[Dict]:
        """Get chat history for a specific user"""
        # This method will be implemented when connecting to the database
        pass 