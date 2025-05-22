from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List

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
    def __init__(self, user_id: str, first_name: str):
        self.user_id = user_id
        self.first_name = first_name
        self.state = States.MAIN_MENU
        self.profile_info: Optional[UserProfile] = None
        self.chat_history: List[Dict] = []
        self.current_analysis: Optional[Dict] = None

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