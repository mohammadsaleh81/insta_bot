from datetime import datetime
from telethon import Button

def calculate_shamsi_age(birth_year: int) -> int:
    """Calculate age based on Persian calendar"""
    current_shamsi_year = 1404  # Current Persian year
    return current_shamsi_year - birth_year

# Button configurations
main_menu_buttons = [
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

coin_purchase_buttons = [
    [Button.inline("💎 ۵۰ سکه - ۵۰,۰۰۰ تومان", b"buy_50_coins")],
    [Button.inline("💎 ۱۰۰ سکه - ۹۰,۰۰۰ تومان", b"buy_100_coins")],
    [Button.inline("💎 ۲۰۰ سکه - ۱۶۰,۰۰۰ تومان", b"buy_200_coins")],
    [Button.inline("🔙 بازگشت", b"back_to_main")]
]

back_to_main_button = [Button.inline("🏠 بازگشت به منوی اصلی", b"back_to_main")]

def format_message_for_chunks(message: str, max_length: int = 4000) -> list:
    """Split long messages into chunks respecting message limits"""
    if len(message) <= max_length:
        return [message]
        
    sections = message.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for section in sections:
        if len(current_chunk) + len(section) + 2 <= max_length:
            current_chunk += section + "\n\n"
        else:
            chunks.append(current_chunk)
            current_chunk = section + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def format_coin_amounts(coins: int) -> str:
    """Format coin amounts with proper separators"""
    return f"{coins:,}"

def format_datetime(dt: datetime) -> str:
    """Format datetime in a consistent way"""
    return dt.strftime("%Y-%m-%d %H:%M:%S") 