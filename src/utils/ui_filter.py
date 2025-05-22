from telethon import events
from telethon.tl.types import Message

class UIMessageFilter:
    """Filter for UI-related messages"""
    
    def __init__(self):
        self.acceptable_list = [
            # Main inline menu items
            "🧠 تحلیل شخصیت",
            "📜 تاریخچه",
            "👤 پروفایل من",
            "💰 خرید سکه",
            "❓ راهنما",
            
            # Back buttons
            "🏠 بازگشت به منوی اصلی",
            "🔙 بازگشت",
            
            # Start/Stop buttons
            "▶️ شروع",
            "⏹ توقف",
            
            # ReplyKeyboard menu items (new persistent keyboard)
            "🔍 جستجو",
            "📺 جدول پخش",
            "🆕 جدیدترین",
            "⭐ محبوب‌ترین",
            "🎬 ژانرها",
            "🌎 کشورها",
            "📆 سال ساخت",
            "📋 لیست دانلود",
            "📞 تماس با ما",
            "❓ راهنما"
        ]
    
    def __call__(self, event):
        """Check if the message text is in the acceptable list"""
        if not isinstance(event.message, Message):
            return False
            
        if not event.message.text:
            return False
            
        return event.message.text in self.acceptable_list

# Create an instance to be imported elsewhere
ui_filter = UIMessageFilter() 