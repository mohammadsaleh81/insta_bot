from telethon import Button

class UIKeyboard:
    """Class to manage the Telegram custom reply keyboard UI"""
    
    def __init__(self):
        # Main keyboard layout with icons and text
        self.main_keyboard_buttons = [
            [
                Button.text("🧠 تحلیل شخصیت"),
                Button.text("📜 تاریخچه")
            ],
            [
                Button.text("👤 پروفایل من"),
                Button.text("💰 خرید سکه")
            ],
            [
                Button.text("❓ راهنما")
            ]
        ]
    
    def get_main_keyboard(self):
        """Get the main menu keyboard"""
        return self.main_keyboard_buttons

# Create an instance to be imported elsewhere
ui_keyboard = UIKeyboard() 