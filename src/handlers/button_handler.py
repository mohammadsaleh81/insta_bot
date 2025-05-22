from telethon import events
from telethon import Button
from utils.ui_keyboard import ui_keyboard

class ButtonHandler:
    """Handler for processing button clicks"""
    
    def __init__(self, client, user_manager):
        self.client = client
        self.user_manager = user_manager
        
        # Define inline buttons
        self.main_menu_buttons = [
            [
                Button.inline("🧠 تحلیل شخصیت", b"start_analysis"),
                Button.inline("📜 تاریخچه", b"view_history")
            ],
            [
                Button.inline("👤 پروفایل من", b"view_profile"),
                Button.inline("💰 خرید سکه", b"buy_coins")
            ],
            [Button.inline("❓ راهنما", b"view_help")]
        ]
        
        self.back_to_main_button = [Button.inline("🏠 بازگشت به منوی اصلی", b"back_to_main")]
    
    def register_handlers(self):
        """Register button callback event handlers"""
        @self.client.on(events.CallbackQuery())
        async def button_callback(event):
            """Process button clicks"""
            user_id = str(event.sender_id)
            data = event.data.decode('utf-8')
            
            # Get current user state
            user_state = self.user_manager.get_user_state(user_id)
            
            # Handle back to main menu button
            if data == "back_to_main":
                # Reset user state to main menu
                self.user_manager.set_user_state(user_id, self.user_manager.States.MAIN_MENU)
                
                # Get user coins
                current_coins = await self.user_manager.get_user_coins(user_id)
                
                # Send main menu message
                await event.edit(
                    f"به منوی اصلی بازگشتید.\n💰 سکه‌های شما: {current_coins}\n\n"
                    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    buttons=self.main_menu_buttons
                )
                
            # Handle other button clicks based on data
            elif data == "start_analysis":
                # Set user state to typing username
                self.user_manager.set_user_state(user_id, self.user_manager.States.TYPING_USERNAME)
                
                # Clear any previous profile info
                self.user_manager.clear_profile_info(user_id)
                
                await event.edit(
                    "👤 لطفاً نام کاربری اینستاگرام مورد نظر را وارد کنید:\n\n"
                    "مثال: @username یا username\n\n"
                    "⚠️ توجه: حساب کاربری باید عمومی (public) باشد.",
                    buttons=self.back_to_main_button
                )
                
            elif data == "view_history":
                # Process view history
                pass
                
            elif data == "view_profile":
                # Process view profile
                pass
                
            elif data == "buy_coins":
                # Process buy coins
                pass
                
            elif data == "view_help":
                # Process view help
                help_text = (
                    "🔍 راهنمای استفاده از ربات:\n\n"
                    "• از کیبورد پایین صفحه برای انتخاب گزینه‌ها استفاده کنید\n"
                    "• برای بازگشت به منوی اصلی، دکمه بازگشت را انتخاب کنید\n"
                    "• برای جستجو، گزینه 🔍 جستجو را انتخاب کنید\n\n"
                    "⚠️ توجه: برخی از قابلیت‌ها ممکن است در دسترس نباشند."
                )
                
                await event.edit(
                    help_text,
                    buttons=self.back_to_main_button
                ) 