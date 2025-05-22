from telethon import events
from telethon import Button
from utils.ui_filter import ui_filter
from utils.ui_keyboard import ui_keyboard

class MessageHandler:
    """Handler for processing text messages"""
    
    def __init__(self, client, user_manager):
        self.client = client
        self.user_manager = user_manager
        self.back_button = [Button.inline("🔙 بازگشت", b"back_to_main")]
    
    def register_handlers(self):
        """Register all message event handlers"""
        # Regular message handler
        @self.client.on(events.NewMessage())
        async def message_handler(event):
            if event.message.text and event.message.text.startswith('/'):
                # Skip command handling - handled by other handlers
                return
                
            # Process user state based messages here
            # ...
        
        # UI Keyboard message handler
        ui_message_handler = events.NewMessage(func=ui_filter)
        @self.client.on(ui_message_handler)
        async def ui_message_processor(event):
            """Process messages from the custom keyboard UI"""
            text = event.message.text
            user_id = str(event.sender_id)
            
            # Get user state from manager
            user_state = self.user_manager.get_user_state(user_id)
            
            # Process keyboard commands
            if text == "🔍 جستجو":
                await event.respond(
                    "🔍 لطفاً عبارت مورد نظر برای جستجو را وارد کنید:",
                    buttons=self.back_button
                )
                self.user_manager.set_user_state(user_id, self.user_manager.States.SEARCHING)
                
            elif text == "📺 جدول پخش":
                await event.respond(
                    "📺 جدول پخش سریال‌های در حال پخش:",
                    buttons=self.back_button
                )
                
            elif text == "🆕 جدیدترین":
                await event.respond(
                    "🆕 جدیدترین محتوای اضافه شده:",
                    buttons=self.back_button
                )
                
            elif text == "⭐ محبوب‌ترین":
                await event.respond(
                    "⭐ محبوب‌ترین و پردانلودترین محتوا:",
                    buttons=self.back_button
                )
                
            elif text == "🎬 ژانرها":
                await event.respond(
                    "🎬 دسته‌بندی محتوا بر اساس ژانر:",
                    buttons=self.back_button
                )
                
            elif text == "🌎 کشورها":
                await event.respond(
                    "🌎 انتخاب محتوا بر اساس کشور سازنده:",
                    buttons=self.back_button
                )
                
            elif text == "📆 سال ساخت":
                await event.respond(
                    "📆 انتخاب محتوا بر اساس سال ساخت:",
                    buttons=self.back_button
                )
                
            elif text == "📋 لیست دانلود":
                await event.respond(
                    "📋 لیست دانلود شما خالی است.",
                    buttons=self.back_button
                )
                
            elif text == "📞 تماس با ما":
                await event.respond(
                    "📞 اطلاعات تماس با ما:\n@AdminContactUsername",
                    buttons=self.back_button
                )
                
            elif text == "❓ راهنما":
                help_text = (
                    "🔍 راهنمای استفاده از ربات:\n\n"
                    "• از کیبورد پایین صفحه برای انتخاب گزینه‌ها استفاده کنید\n"
                    "• برای بازگشت به منوی اصلی، دکمه بازگشت را انتخاب کنید\n"
                    "• برای جستجو، گزینه 🔍 جستجو را انتخاب کنید\n\n"
                    "⚠️ توجه: برخی از قابلیت‌ها ممکن است در دسترس نباشند."
                )
                
                await event.respond(help_text, buttons=self.back_button)