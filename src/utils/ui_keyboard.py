from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRow

class UIKeyboard:
    """Class to manage the Telegram custom reply keyboard UI"""
    
    def __init__(self):
        # Main keyboard layout with icons and text
        self.main_keyboard_buttons = [
            [
                KeyboardButton("🔍 جستجو"),
                KeyboardButton("📅 جدول پخش سریال")
            ],
            [
                KeyboardButton("🆕 جدیدترین ها"),
                KeyboardButton("📚 پردانلودترین ها")
            ],
            [
                KeyboardButton("🌎 کشور ها"),
                KeyboardButton("📂 ژانر ها"),
                KeyboardButton("📆 سال ساخت")
            ],
            [
                KeyboardButton("❓ راهنما"),
                KeyboardButton("📞 تماس با ما"),
                KeyboardButton("📋 لیست دانلود")
            ]
        ]
        
        # Create ReplyKeyboardMarkup for main menu
        self.main_keyboard = ReplyKeyboardMarkup(
            rows=[KeyboardButtonRow(buttons=row) for row in self.main_keyboard_buttons],
            resize=True,
            selective=False,
            placeholder="یک گزینه انتخاب کنید"
        )
    
    def get_main_keyboard(self):
        """Get the main menu keyboard"""
        return self.main_keyboard

# Create an instance to be imported elsewhere
ui_keyboard = UIKeyboard() 