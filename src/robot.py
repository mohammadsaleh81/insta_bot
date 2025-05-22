from telethon import TelegramClient, events, Button
from telethon.tl.types import User as TelegramUser
from telethon.tl.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRow
import logging
import json
import traceback
import os
import asyncio
from datetime import datetime
from insta import get_insta_data, get_insta_posts
from openai import OpenAI
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
from utils.ui_filter import ui_filter
from utils.ui_keyboard import ui_keyboard
from utils.user_manager import UserManager
from models.user import States
# 2025-05-21 20:59:40,714 - __main__ - INFO - ربات شروع به کار کرد.
# بارگیری متغیرهای محیطی
load_dotenv()

# اطلاعات API تلگرام
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')

# هزینه‌های سکه
ANALYSIS_COST = 10  # هزینه هر تحلیل
CHAT_COST = 2      # هزینه هر پیام چت
DEFAULT_COINS = 100  # سکه‌های رایگان اولیه برای کاربران جدید

# تنظیمات لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "insta_analyzer_db"

logger.info(f"اتصال به MongoDB با آدرس: {MONGO_URI}")

# تنظیمات OpenAI
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL'),
    api_key=os.getenv('OPENAI_API_KEY'),
)

# اتصال به MongoDB
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    users_collection = db["users"]
    analysis_collection = db["analysis"]
    
    # بررسی اتصال
    mongo_client.admin.command('ping')
    logger.info("اتصال به MongoDB با موفقیت برقار شد")
    
    # ایجاد ایندکس‌ها در صورت نیاز
    users_collection.create_index([("user_id", 1)], unique=True)
    analysis_collection.create_index([("user_id", 1)])
    analysis_collection.create_index([("created_at", -1)])
    
    # Initialize UserManager
    user_manager = UserManager(mongo_client, DB_NAME)
    
except Exception as e:
    logger.error(f"خطا در اتصال به MongoDB: {str(e)}")
    logger.warning("استفاده از سیستم ذخیره‌سازی فایل به عنوان پشتیبان")

# مسیر ذخیره فایل‌های تاریخچه (برای سازگاری با نسخه قبلی)
HISTORY_DIR = "user_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# دیکشنری برای ذخیره تاریخچه تحلیل‌ها (برای کش)
user_history = {}

# دیکشنری برای ذخیره وضعیت کاربران
user_states = {}

# دیکشنری برای ذخیره اطلاعات پروفایل موقت
user_profile_info = {}

# دیکشنری برای ذخیره تاریخچه چت کاربران با هوش مصنوعی
user_chat_history = {}

# حالت‌های مختلف مکالمه
class States:
    MAIN_MENU = 0
    TYPING_USERNAME = 1
    TYPING_NAME = 2
    TYPING_BIRTH_YEAR = 3
    TYPING_GENDER = 4
    TYPING_CITY = 5
    TYPING_JOB = 6
    TYPING_EVENT = 7
    TYPING_RELATIONSHIP = 8  # افزودن مرحله نوع رابطه
    VIEWING_HISTORY = 9
    VIEWING_PROFILE = 10
    CHATTING_WITH_AI = 11  # حالت چت با هوش مصنوعی
    SEARCHING = 12  # افزودن حالت جستجو

# -----------------------
# ترکیب داده‌های اینستا با داده‌های تکمیلی
async def build_gpt_input(username, extra_info):
    try:
        # دریافت اطلاعات پروفایل و پست‌ها
        profile_data = await get_insta_data(username)
        posts_data = await get_insta_posts(username)

        # پردازش ساده اطلاعات پست‌ها (تا ۵ پست غیر ویدیویی)
        recent_posts = []
        
        if posts_data and 'data' in posts_data:
            count = 0
            for post in posts_data.get("data", []):
                if count >= 5:
                    break
                if post.get("media_type") != "VIDEO":
                    recent_posts.append({
                        "image_description": post.get("caption", "")[:100] or "بدون توضیح تصویری",
                        "caption": post.get("caption", ""),
                        "hashtags": [tag for tag in post.get("caption", "").split() if tag.startswith("#")],
                        "comments": []  # چون فعلاً API کامنت نداری
                    })
                    count += 1

        # اطلاعات بیوگرافی و تصویر پروفایل
        bio = ""
        profile_pic_url = ""
        
        if isinstance(profile_data, dict):
            if 'biography' in profile_data:
                bio = profile_data.get('biography', '')
            elif 'data' in profile_data and 'user' in profile_data['data'] and 'biography' in profile_data['data']['user']:
                bio = profile_data['data']['user'].get('biography', '')
            
            if 'profile_pic_url_hd' in profile_data:
                profile_pic_url = profile_data.get('profile_pic_url_hd', '')
            elif 'data' in profile_data and 'user' in profile_data['data'] and 'profile_pic_url_hd' in profile_data['data']['user']:
                profile_pic_url = profile_data['data']['user'].get('profile_pic_url_hd', '')
                
        # اطلاعات فالوور و فالوینگ
        followers = 0
        following = 0
        
        if isinstance(profile_data, dict):
            if 'edge_followed_by' in profile_data and 'count' in profile_data['edge_followed_by']:
                followers = profile_data['edge_followed_by']['count']
            elif 'data' in profile_data and 'user' in profile_data['data'] and 'edge_followed_by' in profile_data['data']['user']:
                followers = profile_data['data']['user']['edge_followed_by']['count']
                
            if 'edge_follow' in profile_data and 'count' in profile_data['edge_follow']:
                following = profile_data['edge_follow']['count']
            elif 'data' in profile_data and 'user' in profile_data['data'] and 'edge_follow' in profile_data['data']['user']:
                following = profile_data['data']['user']['edge_follow']['count']

        return {
            "structured_data": {
                "name": extra_info.get("name", ""),
                "username": username,
                "birth_year": extra_info.get("birth_year", 0),
                "age_estimate": extra_info.get("age_estimate", 0),
                "gender": extra_info.get("gender", ""),
                "city": extra_info.get("city", ""),
                "job": extra_info.get("job", ""),
                "notable_event": extra_info.get("notable_event", ""),
                "relationship": extra_info.get("relationship", "")
            },
            "profile": {
                "bio": bio,
                "profile_picture_description": profile_pic_url
            },
            "account_stats": {
                "followers": followers,
                "following": following
            },
            "recent_posts": recent_posts,
            "stories": [],  # فعلاً پشتیبانی نشده
            "visual_style": "استایل بصری قابل دریافت از پست‌ها و تصویر پروفایل"
        }
    except Exception as e:
        logger.error(f"خطا در build_gpt_input: {str(e)}")
        traceback.print_exc()
        raise Exception(f"خطا در آماده‌سازی داده‌ها: {str(e)}")

# -----------------------
# ارسال داده به GPT و دریافت تحلیل
async def get_personality_analysis(data_json):
    try:
        prompt = f"""
تو یک تحلیل‌گر شخصیت‌شناسی، سبک ارتباطی و گرایشات روانی-عاطفی هستی.
با توجه به داده‌های زیر، یک تحلیل روان‌شناختی طبقه‌بندی‌شده در ۷ بخش ارائه کن:
۱. هویت روانی و شخصیتی
۲. روابط اجتماعی و عاطفی
۳. گرایشات جنسی و زیبایی‌شناسی بدنی
۴. پوزیشن‌های متناسب با انرژی روانی
۵. فانتزی‌ها و فتیش‌های احتمالی (در صورت وجود)
۶. استراتژی‌های مناسب برای ارتباط با این فرد (با توجه به هدف تحلیل)
۷. جمع‌بندی نهایی

توجه ویژه: در بخش استراتژی‌های ارتباطی، تحلیل خود را با در نظر گرفتن هدف کاربر از تحلیل این پیج ارائه کن. هدف کاربر این است:
"{data_json["structured_data"]["relationship"]}"

با توجه به این هدف، راهکارهای خاص و عملی برای رسیدن به هدف مورد نظر ارائه کن که متناسب با ویژگی‌های شخصیتی فرد تحلیل شده باشد. به نقاط قوت و ضعف احتمالی در این نوع ارتباط نیز اشاره کن.

اطلاعات:
{json.dumps(data_json, ensure_ascii=False, indent=2)}
"""

        logger.info("در حال ارسال درخواست به OpenAI API...")
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-r1:free",
                messages=[
                    {"role": "system", "content": "تو یک تحلیل‌گر شخصیت‌شناسی حرفه‌ای هستی که تحلیل‌های دقیق و کاربردی ارائه می‌دهد."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=120
            )

            if not response:
                raise Exception("پاسخی از API دریافت نشد")

            # بررسی ساختار پاسخ
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message'):
                    return response.choices[0].message.content
                elif hasattr(response.choices[0], 'text'):
                    return response.choices[0].text
                else:
                    logger.error(f"ساختار پاسخ نامعتبر است: {response}")
                    raise Exception("ساختار پاسخ API نامعتبر است")
            else:
                logger.error(f"پاسخ API فاقد محتوا است: {response}")
                raise Exception("پاسخ API فاقد محتوا است")

        except Exception as api_error:
            logger.error(f"خطا در ارتباط با OpenAI API: {str(api_error)}")
            raise Exception(f"خطا در ارتباط با API: {str(api_error)}")
        
    except Exception as e:
        logger.error(f"خطا در get_personality_analysis: {str(e)}")
        traceback.print_exc()
        raise Exception(f"خطا در دریافت تحلیل شخصیت: {str(e)}")

# -----------------------
# ذخیره تحلیل در تاریخچه کاربر و پایگاه داده
async def save_analysis_to_history(user_id, username, analysis):
    """ذخیره تحلیل در تاریخچه کاربر و پایگاه داده"""
    user_id_str = str(user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ذخیره در حافظه کش
    if user_id_str not in user_history:
        user_history[user_id_str] = []
    
    # افزودن تحلیل جدید به ابتدای لیست (جدیدترین در ابتدا)
    analysis_data = {
        "timestamp": timestamp,
        "username": username,
        "analysis": analysis[:100] + "..."  # ذخیره خلاصه تحلیل
    }
    
    user_history[user_id_str].insert(0, analysis_data)
    
    # محدود کردن تعداد تاریخچه‌ها به ۱۰ مورد در کش
    user_history[user_id_str] = user_history[user_id_str][:10]
    
    # ذخیره در پایگاه داده MongoDB
    analysis_document = {
        "user_id": user_id_str,
        "username": username,
        "timestamp": timestamp,
        "analysis": analysis,
        "created_at": datetime.now()
    }
    
    try:
        # ذخیره در MongoDB
        analysis_collection.insert_one(analysis_document)
        logger.info(f"تحلیل برای {username} در پایگاه داده ذخیره شد")
        
        # بروزرسانی اطلاعات کاربر
        users_collection.update_one(
            {"user_id": user_id_str},
            {"$inc": {"analysis_count": 1}, "$set": {"last_activity": datetime.now()}},
            upsert=True
        )
        
    except Exception as e:
        logger.error(f"خطا در ذخیره‌سازی در پایگاه داده: {str(e)}")
        
        # در صورت خطا، از روش قبلی فایل استفاده می‌کنیم
        filename = f"{HISTORY_DIR}/{user_id_str}_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": analysis_data["timestamp"],
                "username": username,
                "analysis": analysis
            }, f, ensure_ascii=False, indent=2)

# ذخیره کاربر در پایگاه داده
async def save_user_to_db(user_id, first_name, last_name=None, username=None, lang_code=None):
    """ذخیره یا بروزرسانی اطلاعات کاربر در پایگاه داده"""
    user_id_str = str(user_id)
    
    user_data = {
        "user_id": user_id_str,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "lang_code": lang_code,
        "last_activity": datetime.now()
    }
    
    # اگر کاربر قبلاً وجود داشته، اطلاعات او بروزرسانی می‌شود
    try:
        users_collection.update_one(
            {"user_id": user_id_str},
            {"$set": user_data},
            upsert=True
        )
        logger.info(f"اطلاعات کاربر {user_id_str} در پایگاه داده بروزرسانی شد")
    except Exception as e:
        logger.error(f"خطا در ذخیره‌سازی اطلاعات کاربر: {str(e)}")

# بازیابی تاریخچه تحلیل‌های کاربر از پایگاه داده
async def load_user_history(user_id):
    """بازیابی تاریخچه تحلیل‌های کاربر از پایگاه داده"""
    user_id_str = str(user_id)
    
    if user_id_str in user_history:
        # استفاده از کش اگر موجود باشد
        return user_history[user_id_str]
    
    try:
        # جستجو در MongoDB
        cursor = analysis_collection.find(
            {"user_id": user_id_str},
            {"username": 1, "timestamp": 1, "analysis": {"$substr": ["$analysis", 0, 100]}}
        ).sort("created_at", -1).limit(10)
        
        history_items = []
        for doc in cursor:  # حذف async
            history_items.append({
                "timestamp": doc.get("timestamp", ""),
                "username": doc.get("username", ""),
                "analysis": doc.get("analysis", "") + "..."
            })
        
        # ذخیره در کش
        user_history[user_id_str] = history_items
        return history_items
        
    except Exception as e:
        logger.error(f"خطا در بازیابی تاریخچه از پایگاه داده: {str(e)}")
        
        # تلاش برای بازیابی از روش قدیمی فایل
        history_items = []
        import glob
        pattern = f"{HISTORY_DIR}/{user_id_str}_*.json"
        matching_files = glob.glob(pattern)
        
        for file_path in matching_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history_items.append({
                        "timestamp": data.get("timestamp", ""),
                        "username": data.get("username", ""),
                        "analysis": data.get("analysis", "")[:100] + "..."
                    })
            except Exception as file_error:
                logger.error(f"خطا در خواندن فایل {file_path}: {str(file_error)}")
        
        # مرتب‌سازی بر اساس تاریخ (جدیدترین اول)
        history_items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # محدود کردن به ۱۰ مورد
        history_items = history_items[:10]
        
        # ذخیره در کش
        user_history[user_id_str] = history_items
        return history_items

# -----------------------
# محاسبه سن بر اساس سال شمسی
def calculate_shamsi_age(birth_year):
    """محاسبه سن بر اساس سال شمسی"""
    current_shamsi_year = 1404  # سال شمسی فعلی
    return current_shamsi_year - birth_year

# مدیریت سکه‌ها
async def get_user_coins(user_id):
    """دریافت تعداد سکه‌های کاربر"""
    try:
        user_doc = users_collection.find_one({"user_id": str(user_id)})
        if user_doc:
            return user_doc.get("coins", 0)
        return 0
    except Exception as e:
        logger.error(f"خطا در دریافت سکه‌های کاربر: {str(e)}")
        return 0

async def update_user_coins(user_id, coins):
    """بروزرسانی تعداد سکه‌های کاربر"""
    try:
        users_collection.update_one(
            {"user_id": str(user_id)},
            {"$set": {"coins": coins}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"خطا در بروزرسانی سکه‌های کاربر: {str(e)}")
        return False

async def deduct_coins(user_id, amount):
    """کم کردن سکه از کاربر"""
    current_coins = await get_user_coins(user_id)
    if current_coins >= amount:
        new_coins = current_coins - amount
        success = await update_user_coins(user_id, new_coins)
        return success, new_coins
    return False, current_coins

async def add_coins(user_id, amount):
    """اضافه کردن سکه به کاربر"""
    current_coins = await get_user_coins(user_id)
    new_coins = current_coins + amount
    success = await update_user_coins(user_id, new_coins)
    return success, new_coins

# دکمه‌های منوی اصلی
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

# دکمه‌های منوی اصلی با کیبورد ثابت (مشابه تصویر)
# استفاده از کیبورد تعریف شده در ui_keyboard
main_keyboard_buttons = ui_keyboard.get_main_keyboard()

# دکمه‌های خرید سکه
coin_purchase_buttons = [
    [Button.inline("💎 ۵۰ سکه - ۵۰,۰۰۰ تومان", b"buy_50_coins")],
    [Button.inline("💎 ۱۰۰ سکه - ۹۰,۰۰۰ تومان", b"buy_100_coins")],
    [Button.inline("💎 ۲۰۰ سکه - ۱۶۰,۰۰۰ تومان", b"buy_200_coins")],
    [Button.inline("🔙 بازگشت", b"back_to_main")]
]

# دکمه بازگشت به منوی اصلی
back_to_main_button = [Button.inline("🏠 بازگشت به منوی اصلی", b"back_to_main")]

# -----------------------
# ایجاد کلاینت تلگرام
bot = TelegramClient('insta_analyzer_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# -----------------------
# رویداد شروع مکالمه
@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    """پاسخ به دستور شروع"""
    sender = await event.get_sender()
    user_id = str(sender.id)
    
    # تنظیم وضعیت کاربر به منوی اصلی
    user_manager.set_user_state(user_id, States.MAIN_MENU)
    
    # بررسی اگر کاربر جدید است
    user_doc = users_collection.find_one({"user_id": user_id})
    is_new_user = not user_doc
    
    if is_new_user:
        # اضافه کردن سکه‌های رایگان اولیه برای کاربران جدید
        await user_manager.update_user_coins(user_id, DEFAULT_COINS)
    
    # ذخیره اطلاعات کاربر در پایگاه داده
    await user_manager.save_user(
        user_id, 
        sender.first_name, 
        sender.last_name if hasattr(sender, 'last_name') else None,
        sender.username if hasattr(sender, 'username') else None,
        sender.lang_code if hasattr(sender, 'lang_code') else None
    )
    
    # دریافت تعداد سکه‌های فعلی
    current_coins = await user_manager.get_user_coins(user_id)
    
    # ارسال تصویر خوش‌آمدگویی
    welcome_photo = "welcome_banner.jpg"  # مسیر تصویر خوش‌آمدگویی
    
    welcome_message = f"سلام {sender.first_name}! 👋\n\n"
    
    if is_new_user:
        welcome_message += f"🎁 به عنوان هدیه خوش‌آمدگویی {DEFAULT_COINS} سکه رایگان دریافت کردید!\n\n"
    
    welcome_message += (
        "به ربات تحلیل شخصیت اینستاگرام خوش آمدید! 🔍\n\n"
        "این ربات با دریافت اکانت اینستاگرام و اطلاعات تکمیلی، یک تحلیل شخصیت ارائه می‌کند.\n\n"
        f"💰 سکه‌های شما: {current_coins}\n"
        f"💡 هر تحلیل {ANALYSIS_COST} سکه و هر پیام چت {CHAT_COST} سکه هزینه دارد.\n\n"
        "از منوی زیر انتخاب کنید:"
    )
    
    # Get the keyboard buttons
    keyboard_buttons = ui_keyboard.get_main_keyboard()
    markup = event.client.build_reply_markup(keyboard_buttons)
    
    try:
        # ارسال تصویر و منو
        await bot.send_file(
            event.chat_id,
            welcome_photo,
            caption=welcome_message,
            buttons=markup
        )
    except Exception as e:
        # اگر ارسال تصویر با خطا مواجه شد، فقط متن و منو را ارسال کن
        await event.respond(welcome_message, buttons=markup)

# -----------------------
# رویداد راهنما
@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    """پاسخ به دستور راهنما"""
    help_text = (
        "🔍 راهنمای ربات تحلیل شخصیت اینستاگرام:\n\n"
        "این ربات با دریافت نام کاربری اینستاگرام و اطلاعات تکمیلی، "
        "یک تحلیل روانشناختی از شخصیت فرد ارائه می‌دهد.\n\n"
        "📋 امکانات ربات:\n"
        "• تحلیل شخصیت: بر اساس پروفایل اینستاگرام و اطلاعات تکمیلی\n"
        "• تاریخچه تحلیل‌ها: مشاهده تحلیل‌های پیشین\n"
        "• اطلاعات کاربری: مشاهده اطلاعات حساب کاربری شما\n\n"
        "🔸 روند کار تحلیل شخصیت:\n"
        "1. دریافت نام کاربری اینستاگرام\n"
        "2. دریافت اطلاعات تکمیلی (نام، سن، شهر و...)\n"
        "3. تحلیل داده‌ها و ارائه نتیجه\n\n"
        "⚠️ نکته: اطلاعات دقیق‌تر منجر به تحلیل بهتر می‌شود."
    )
    
    await event.respond(help_text, buttons=back_to_main_button)

# -----------------------
# رویداد لغو مکالمه
@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel_command(event):
    """لغو عملیات فعلی و بازگشت به منوی اصلی"""
    sender = await event.get_sender()
    user_id = str(sender.id)
    
    # تنظیم وضعیت کاربر به منوی اصلی
    user_manager.set_user_state(user_id, States.MAIN_MENU)
    
    # پاک کردن اطلاعات کاربر اگر وجود داشت
    if user_id in user_profile_info:
        del user_profile_info[user_id]
    
    # Get the keyboard buttons
    keyboard_buttons = ui_keyboard.get_main_keyboard()
    markup = event.client.build_reply_markup(keyboard_buttons)
    
    await event.respond(
        "عملیات لغو شد. به منوی اصلی بازگشتید.",
        buttons=markup
    )

# -----------------------
# رویداد دکمه‌ها
@bot.on(events.CallbackQuery())
async def button_callback(event):
    """پاسخ به کلیک روی دکمه‌ها"""
    sender = await event.get_sender()
    user_id = str(sender.id)
    data = event.data.decode('utf-8')
    
    # دریافت وضعیت فعلی کاربر
    state = user_manager.get_user_state(user_id)
    
    if data == "back_to_main":
        user_manager.set_user_state(user_id, States.MAIN_MENU)
        current_coins = await user_manager.get_user_coins(user_id)
        await event.edit(
            f"به منوی اصلی بازگشتید.\n💰 سکه‌های شما: {current_coins}\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            buttons=main_menu_buttons
        )
    
    elif data == "start_analysis":
        # تنظیم وضعیت کاربر به حالت دریافت نام کاربری
        user_manager.set_user_state(user_id, States.TYPING_USERNAME)
        
        # پاک کردن اطلاعات قبلی اگر وجود داشته باشد
        user_manager.clear_profile_info(user_id)
            
        await event.edit(
            "👤 لطفاً نام کاربری اینستاگرام مورد نظر را وارد کنید:\n\n"
            "مثال: @username یا username\n\n"
            "⚠️ توجه: حساب کاربری باید عمومی (public) باشد.",
            buttons=back_to_main_button
        )
    
    elif data == "confirm_analysis":
        # بررسی اعتبار سکه‌ها
        current_coins = await user_manager.get_user_coins(user_id)
        
        if current_coins < ANALYSIS_COST:
            await event.edit(
                f"❌ سکه‌های شما کافی نیست!\n\n"
                f"💰 سکه‌های فعلی: {current_coins}\n"
                f"💎 سکه‌های مورد نیاز: {ANALYSIS_COST}\n\n"
                "لطفاً ابتدا سکه خریداری کنید.",
                buttons=[
                    [Button.inline("💰 خرید سکه", b"buy_coins")],
                    back_to_main_button
                ]
            )
            return
        
        # کم کردن سکه‌ها
        success, new_coins = await user_manager.deduct_coins(user_id, ANALYSIS_COST)
        
        if not success:
            await event.edit(
                "❌ خطا در کسر سکه‌ها. لطفاً مجدداً تلاش کنید.",
                buttons=back_to_main_button
            )
            return
        
        # دریافت اطلاعات پروفایل
        profile_info = user_manager.get_profile_info(user_id)
        username = profile_info.get("username", "")
        
        # اطلاع‌رسانی به کاربر
        await event.edit(
            f"⏳ در حال تحلیل پروفایل {username}...\n\n"
            f"💰 {ANALYSIS_COST} سکه از حساب شما کسر شد. سکه‌های باقیمانده: {new_coins}\n\n"
            "لطفاً کمی صبر کنید. این فرایند ممکن است تا ۲ دقیقه طول بکشد."
        )
        
        try:
            # ساخت ورودی برای تحلیل
            gpt_input = await build_gpt_input(username, profile_info)
            
            # دریافت تحلیل
            analysis = await get_personality_analysis(gpt_input)
            
            # ذخیره تحلیل در تاریخچه
            await user_manager.save_analysis(user_id, username, analysis)
            
            # ارسال نتیجه تحلیل به صورت چند پیام (به دلیل محدودیت طول پیام تلگرام)
            await event.respond(f"📊 تحلیل شخصیت برای {username}:")
            
            max_length = 4000
            sections = analysis.split('\n\n')
            current_message = ""
            
            for section in sections:
                if len(current_message) + len(section) + 2 <= max_length:
                    current_message += section + "\n\n"
                else:
                    await event.respond(current_message)
                    current_message = section + "\n\n"
            
            if current_message:
                await event.respond(current_message)
            
            # ارسال دکمه‌های پایانی
            final_buttons = [
                [Button.inline("🔄 تحلیل پروفایل دیگر", b"start_analysis")],
                [Button.inline("📜 مشاهده تاریخچه", b"view_history")],
                back_to_main_button
            ]
            
            await event.respond(
                "✅ تحلیل با موفقیت انجام شد!\n\n"
                f"💰 سکه‌های باقیمانده: {new_coins}",
                buttons=final_buttons
            )
            
        except Exception as e:
            logger.error(f"خطا در تحلیل پروفایل: {str(e)}")
            
            # بازگرداندن سکه‌ها در صورت خطا
            await user_manager.add_coins(user_id, ANALYSIS_COST)
            
            await event.respond(
                f"❌ خطا در تحلیل پروفایل:\n{str(e)}\n\n"
                "سکه‌های شما بازگردانده شد. لطفاً مجدداً تلاش کنید.",
                buttons=back_to_main_button
            )
    
    elif data == "edit_profile_info":
        # نمایش منوی ویرایش اطلاعات
        edit_buttons = [
            [Button.inline("👤 ویرایش نام کاربری", b"edit_username")],
            [Button.inline("📋 ویرایش نام", b"edit_name")],
            [Button.inline("🎂 ویرایش سال تولد", b"edit_birth_year")],
            [Button.inline("👫 ویرایش جنسیت", b"edit_gender")],
            [Button.inline("🏙 ویرایش شهر", b"edit_city")],
            [Button.inline("💼 ویرایش شغل", b"edit_job")],
            [Button.inline("🔍 ویرایش هدف تحلیل", b"edit_relationship")],
            back_to_main_button
        ]
        
        await event.edit(
            "✏️ لطفاً اطلاعاتی که می‌خواهید ویرایش کنید را انتخاب کنید:",
            buttons=edit_buttons
        )
    
    elif data.startswith("edit_"):
        # پردازش درخواست‌های ویرایش اطلاعات
        field = data.replace("edit_", "")
        
        field_names = {
            "username": "نام کاربری",
            "name": "نام",
            "birth_year": "سال تولد",
            "gender": "جنسیت",
            "city": "شهر",
            "job": "شغل",
            "relationship": "هدف تحلیل"
        }
        
        field_states = {
            "username": States.TYPING_USERNAME,
            "name": States.TYPING_NAME,
            "birth_year": States.TYPING_BIRTH_YEAR,
            "gender": States.TYPING_GENDER,
            "city": States.TYPING_CITY,
            "job": States.TYPING_JOB,
            "relationship": States.TYPING_RELATIONSHIP
        }
        
        if field in field_states:
            # تنظیم وضعیت کاربر به حالت ویرایش فیلد مورد نظر
            user_manager.set_user_state(user_id, field_states[field])
            
            await event.edit(
                f"✏️ لطفاً {field_names.get(field, field)} جدید را وارد کنید:",
                buttons=back_to_main_button
            )
    
    elif data == "view_history":
        # دریافت تاریخچه تحلیل‌های کاربر
        history_items = await user_manager.get_user_history(user_id)
        
        if not history_items:
            await event.edit(
                "📌 شما هنوز هیچ تحلیلی انجام نداده‌اید.\n\n"
                "برای شروع، از گزینه 'تحلیل شخصیت' استفاده کنید.",
                buttons=back_to_main_button
            )
            return
            
        history_text = "📜 تاریخچه تحلیل‌های شما:\n\nبر روی هر مورد کلیک کنید تا تحلیل کامل را مشاهده کنید:\n\n"
        
        # ساخت دکمه برای هر مورد تاریخچه
        buttons = []
        for i, item in enumerate(history_items):
            display_text = f"📊 {item['username']} - {item['timestamp']}"
            # ساخت یک کلید منحصر به فرد برای هر تحلیل
            history_key = f"history_{user_id}_{item['username']}_{item['timestamp'].replace(' ', '_').replace(':', '-')}"
            buttons.append([Button.inline(display_text, history_key.encode())])
        
        # اضافه کردن دکمه بازگشت به منوی اصلی
        buttons.append(back_to_main_button)
        
        await event.edit(history_text, buttons=buttons)
    
    elif data == "view_profile":
        # دریافت اطلاعات کاربر
        current_coins = await user_manager.get_user_coins(user_id)
        user_info = await user_manager.get_user_info(user_id)
        
        if not user_info:
            user_info = {
                "first_name": sender.first_name,
                "analysis_count": 0,
                "join_date": datetime.now().strftime("%Y-%m-%d"),
                "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        
        profile_text = (
            f"👤 **پروفایل کاربری**\n\n"
            f"🆔 شناسه: `{user_id}`\n"
            f"👤 نام: {user_info['first_name']}\n"
            f"💰 سکه‌های شما: {current_coins}\n\n"
            f"📊 **آمار استفاده**\n"
            f"📈 تعداد تحلیل‌ها: {user_info['analysis_count']}\n"
            f"📅 تاریخ عضویت: {user_info['join_date']}\n"
            f"⏱ آخرین فعالیت: {user_info['last_activity']}\n\n"
            "برای خرید سکه، روی دکمه 'خرید سکه' کلیک کنید."
        )
        
        profile_buttons = [
            [Button.inline("💰 خرید سکه", b"buy_coins")],
            back_to_main_button
        ]
        
        await event.edit(profile_text, buttons=profile_buttons)
    
    elif data == "buy_coins":
        coins_text = (
            "💎 **خرید سکه**\n\n"
            "لطفاً یکی از بسته‌های زیر را انتخاب کنید:\n\n"
            "پس از پرداخت و تایید ادمین، سکه‌ها به حساب شما اضافه خواهند شد."
        )
        
        await event.edit(coins_text, buttons=coin_purchase_buttons)
    
    elif data.startswith("buy_") and "_coins" not in data:
        amount = int(data.split("_")[1])
        price = {
            50: "50,000",
            100: "90,000",
            200: "160,000"
        }.get(amount, "نامشخص")
        
        payment_text = (
            f"💎 **خرید {amount} سکه**\n\n"
            f"💰 مبلغ قابل پرداخت: {price} تومان\n\n"
            "🏦 اطلاعات پرداخت:\n"
            "شماره کارت: 6037-9975-9973-3381\n"
            "به نام: علی محمدی\n\n"
            "پس از واریز:\n"
            "1️⃣ تصویر رسید پرداخت را به پشتیبانی ارسال کنید:\n"
            "@InstaAnalysAiSupport\n"
            "2️⃣ منتظر تایید و اضافه شدن سکه‌ها باشید\n\n"
            "⚠️ لطفاً دقیقاً مبلغ ذکر شده را واریز کنید."
        )
        
        payment_buttons = [
            [Button.inline("🔙 بازگشت به لیست بسته‌ها", b"buy_coins")],
            back_to_main_button
        ]
        
        await event.edit(payment_text, buttons=payment_buttons)
    
    elif data == "view_help":
        help_text = (
            "❓ **راهنمای ربات**\n\n"
            "🤖 **قابلیت‌های ربات:**\n"
            "• تحلیل شخصیت از روی پروفایل اینستاگرام\n"
            "• تحلیل رفتار و علایق از محتوای پست‌ها\n"
            "• ارائه گزارش جامع روانشناسی\n\n"
            "💰 **سیستم سکه:**\n"
            f"• هر تحلیل: {ANALYSIS_COST} سکه\n"
            f"• هر پیام چت: {CHAT_COST} سکه\n"
            "• امکان خرید سکه از منوی پروفایل\n\n"
            "⚠️ **نکات مهم:**\n"
            "• پروفایل اینستاگرام باید عمومی باشد\n"
            "• اطلاعات وارد شده باید دقیق باشد\n"
            "• تحلیل‌ها در تاریخچه ذخیره می‌شوند\n\n"
            "🆘 **پشتیبانی:**\n"
            "برای ارتباط با پشتیبانی: @InstaAnalysAiSupport"
        )
        
        help_buttons = [
            [Button.inline("📝 شروع تحلیل", b"start_analysis")],
            back_to_main_button
        ]
        
        await event.edit(help_text, buttons=help_buttons)

# -----------------------
# نمایش تحلیل از تاریخچه
async def show_analysis_from_history(event, user_id, username, timestamp):
    """نمایش تحلیل ذخیره شده از تاریخچه"""
    try:
        # ابتدا تلاش برای یافتن در پایگاه داده
        try:
            # جستجو در MongoDB
            analysis_doc = analysis_collection.find_one({
                "user_id": user_id,
                "username": username,
                "timestamp": timestamp
            })
            
            if analysis_doc:
                analysis = analysis_doc.get("analysis", "")
                logger.info(f"تحلیل از پایگاه داده MongoDB بازیابی شد")
            else:
                # اگر تحلیل دقیق یافت نشد، آخرین تحلیل این کاربر را نمایش می‌دهیم
                analysis_doc = analysis_collection.find_one(
                    {"user_id": user_id, "username": username},
                    sort=[("created_at", -1)]
                )
                
                if analysis_doc:
                    analysis = analysis_doc.get("analysis", "")
                    timestamp = analysis_doc.get("timestamp", timestamp)
                    logger.info(f"آخرین تحلیل کاربر {username} از پایگاه داده بازیابی شد")
                else:
                    analysis = None
        except Exception as db_error:
            logger.error(f"خطا در بازیابی از پایگاه داده: {str(db_error)}")
            analysis = None
        
        # اگر در پایگاه داده یافت نشد، از فایل‌ها جستجو می‌کنیم
        if not analysis:
            import glob
            import os
            
            logger.info(f"تلاش برای یافتن تحلیل در فایل‌ها")
            
            # جستجو در دایرکتوری تاریخچه
            pattern = f"{HISTORY_DIR}/{user_id}_{username}_*.json"
            matching_files = glob.glob(pattern)
            
            if not matching_files:
                all_files = glob.glob(f"{HISTORY_DIR}/*.json")
                logger.info(f"هیچ فایلی برای الگوی {pattern} یافت نشد. فایل‌های موجود: {len(all_files)}")
                
                await event.edit(
                    f"❌ تحلیل برای کاربر {username} یافت نشد.",
                    buttons=back_to_main_button
                )
                return
            
            logger.info(f"فایل‌های یافت شده: {len(matching_files)}")
            
            # فایل‌ها را بر اساس زمان ایجاد مرتب می‌کنیم (جدیدترین اول)
            matching_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            target_file = matching_files[0]
            
            # خواندن محتوای فایل
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                analysis = data.get("analysis", "")
                timestamp = data.get("timestamp", timestamp)
        
        if not analysis:
            await event.edit(
                f"❌ محتوای تحلیل یافت نشد.",
                buttons=back_to_main_button
            )
            return
        
        # نمایش تحلیل
        await event.edit(f"📊 تحلیل شخصیت برای {username} ({timestamp}):")
        
        # ارسال نتیجه تحلیل به صورت چند پیام (به دلیل محدودیت طول پیام تلگرام)
        max_length = 4000
        sections = analysis.split('\n\n')
        current_message = ""
        
        for section in sections:
            if len(current_message) + len(section) + 2 <= max_length:
                current_message += section + "\n\n"
            else:
                await event.respond(current_message)
                current_message = section + "\n\n"
        
        if current_message:
            await event.respond(current_message)
        
        # ارسال دکمه بازگشت به تاریخچه و منوی اصلی
        buttons = [
            [Button.inline("🔙 بازگشت به تاریخچه", b"view_history")],
            [Button.inline("🏠 بازگشت به منوی اصلی", b"back_to_main")]
        ]
        
        await event.respond(
            "پایان تحلیل",
            buttons=buttons
        )
        
    except Exception as e:
        logger.error(f"خطا در نمایش تحلیل از تاریخچه: {str(e)}")
        traceback.print_exc()
        
        # نمایش جزئیات خطا برای دیباگ
        error_details = f"❌ خطا در بازیابی تحلیل: {str(e)}\nنوع خطا: {type(e).__name__}"
        
        await event.edit(
            error_details,
            buttons=back_to_main_button
        )

# -----------------------
# پردازش پیام‌های مربوط به منوی اصلی
async def ui_message_processor(update):
    """پردازش پیام‌های منوی UI"""
    received = update.message.text
    user_id = str(update.sender_id)

    # دریافت وضعیت فعلی کاربر
    user_state = user_manager.get_user_state(user_id)
        
    if received == "🧠 تحلیل شخصیت":
        # تنظیم وضعیت کاربر به حالت دریافت نام کاربری
        user_manager.set_user_state(user_id, States.TYPING_USERNAME)
        
        # پاک کردن اطلاعات قبلی اگر وجود داشته باشد
        user_manager.clear_profile_info(user_id)
            
        await update.respond(
            "👤 لطفاً نام کاربری اینستاگرام مورد نظر را وارد کنید:\n\n"
            "مثال: @username یا username\n\n"
            "⚠️ توجه: حساب کاربری باید عمومی (public) باشد.",
            buttons=back_to_main_button
        )
    elif received == "📜 تاریخچه":
        # دریافت تاریخچه تحلیل‌های کاربر
        history_items = await user_manager.get_user_history(user_id)
        
        if not history_items:
            await update.respond(
                "📌 شما هنوز هیچ تحلیلی انجام نداده‌اید.\n\n"
                "برای شروع، از گزینه 'تحلیل شخصیت' استفاده کنید.",
                buttons=back_to_main_button
            )
            return
            
        history_text = "📜 تاریخچه تحلیل‌های شما:\n\nبر روی هر مورد کلیک کنید تا تحلیل کامل را مشاهده کنید:\n\n"
        
        # ساخت دکمه برای هر مورد تاریخچه
        buttons = []
        for i, item in enumerate(history_items):
            display_text = f"📊 {item['username']} - {item['timestamp']}"
            # ساخت یک کلید منحصر به فرد برای هر تحلیل
            history_key = f"history_{user_id}_{item['username']}_{item['timestamp'].replace(' ', '_').replace(':', '-')}"
            buttons.append([Button.inline(display_text, history_key.encode())])
        
        # اضافه کردن دکمه بازگشت به منوی اصلی
        buttons.append(back_to_main_button)
        
        await update.respond(history_text, buttons=buttons)
    elif received == "👤 پروفایل من":
        # دریافت اطلاعات کاربر
        current_coins = await user_manager.get_user_coins(user_id)
        user_info = await user_manager.get_user_info(user_id)
        
        if not user_info:
            user_info = {
                "first_name": update.sender.first_name if hasattr(update.sender, "first_name") else "",
                "analysis_count": 0,
                "join_date": datetime.now().strftime("%Y-%m-%d"),
                "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        
        profile_text = (
            f"👤 **پروفایل کاربری**\n\n"
            f"🆔 شناسه: `{user_id}`\n"
            f"👤 نام: {user_info['first_name']}\n"
            f"💰 سکه‌های شما: {current_coins}\n\n"
            f"📊 **آمار استفاده**\n"
            f"📈 تعداد تحلیل‌ها: {user_info['analysis_count']}\n"
            f"📅 تاریخ عضویت: {user_info['join_date']}\n"
            f"⏱ آخرین فعالیت: {user_info['last_activity']}\n\n"
            "برای خرید سکه، روی دکمه 'خرید سکه' کلیک کنید."
        )
        
        profile_buttons = [
            [Button.inline("💰 خرید سکه", b"buy_coins")],
            back_to_main_button
        ]
        
        await update.respond(profile_text, buttons=profile_buttons)
    elif received == "💰 خرید سکه":
        coins_text = (
            "💎 **خرید سکه**\n\n"
            "لطفاً یکی از بسته‌های زیر را انتخاب کنید:\n\n"
            "پس از پرداخت و تایید ادمین، سکه‌ها به حساب شما اضافه خواهند شد."
        )
        
        await update.respond(coins_text, buttons=coin_purchase_buttons)
    elif received == "❓ راهنما":
        help_text = (
            "❓ **راهنمای ربات**\n\n"
            "🤖 **قابلیت‌های ربات:**\n"
            "• تحلیل شخصیت از روی پروفایل اینستاگرام\n"
            "• تحلیل رفتار و علایق از محتوای پست‌ها\n"
            "• ارائه گزارش جامع روانشناسی\n\n"
            "💰 **سیستم سکه:**\n"
            f"• هر تحلیل: {ANALYSIS_COST} سکه\n"
            f"• هر پیام چت: {CHAT_COST} سکه\n"
            "• امکان خرید سکه از منوی پروفایل\n\n"
            "⚠️ **نکات مهم:**\n"
            "• پروفایل اینستاگرام باید عمومی باشد\n"
            "• اطلاعات وارد شده باید دقیق باشد\n"
            "• تحلیل‌ها در تاریخچه ذخیره می‌شوند\n\n"
            "🆘 **پشتیبانی:**\n"
            "برای ارتباط با پشتیبانی: @InstaAnalysAiSupport"
        )
        
        help_buttons = [
            [Button.inline("📝 شروع تحلیل", b"start_analysis")],
            back_to_main_button
        ]
        
        await update.respond(help_text, buttons=help_buttons)

# -----------------------
# رویداد پیام‌های متنی (غیر از دستورات و منوها)
@bot.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/') and not ui_filter(e)))
async def text_message_handler(event):
    """پردازش پیام‌های متنی بر اساس وضعیت کاربر"""
    sender = await event.get_sender()
    user_id = str(sender.id)
    text = event.text.strip()
    
    # دریافت وضعیت فعلی کاربر
    state = user_manager.get_user_state(user_id)
    
    # پردازش بر اساس وضعیت کاربر
    if state == States.TYPING_USERNAME:
        # دریافت نام کاربری اینستاگرام
        username = text.replace("@", "").strip()
        
        if not username:
            await event.respond(
                "❌ نام کاربری وارد شده معتبر نیست. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # ذخیره نام کاربری در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "username", username)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_NAME)
        
        await event.respond(
            f"✅ نام کاربری «{username}» ثبت شد.\n\n"
            "لطفاً نام کامل شخص مورد نظر را وارد کنید:",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_NAME:
        # دریافت نام کامل
        name = text.strip()
        
        if not name:
            await event.respond(
                "❌ نام وارد شده معتبر نیست. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # ذخیره نام در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "name", name)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_BIRTH_YEAR)
        
        await event.respond(
            f"✅ نام «{name}» ثبت شد.\n\n"
            "لطفاً سال تولد شخص مورد نظر را به صورت عدد شمسی وارد کنید (مثلاً ۱۳۷۵):",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_BIRTH_YEAR:
        # دریافت سال تولد
        try:
            birth_year = int(text.strip())
            
            # اعتبارسنجی ساده برای سال تولد
            if birth_year < 1300 or birth_year > 1410:
                raise ValueError("Invalid birth year")
            
            # محاسبه سن
            age = calculate_shamsi_age(birth_year)
            
            # ذخیره سال تولد و سن در اطلاعات پروفایل
            user_manager.set_profile_info(user_id, "birth_year", birth_year)
            user_manager.set_profile_info(user_id, "age_estimate", age)
            
            # تغییر وضعیت به مرحله بعدی
            user_manager.set_user_state(user_id, States.TYPING_GENDER)
            
            await event.respond(
                f"✅ سال تولد «{birth_year}» (سن تقریبی: {age} سال) ثبت شد.\n\n"
                "لطفاً جنسیت شخص مورد نظر را مشخص کنید (مرد/زن):",
                buttons=back_to_main_button
            )
        except:
            await event.respond(
                "❌ سال تولد وارد شده معتبر نیست. لطفاً یک عدد شمسی معتبر (مثلاً ۱۳۷۵) وارد کنید:",
                buttons=back_to_main_button
            )
    
    elif state == States.TYPING_GENDER:
        # دریافت جنسیت
        gender = text.strip().lower()
        
        if gender not in ["مرد", "زن", "مذکر", "مونث", "آقا", "خانم"]:
            await event.respond(
                "❌ جنسیت وارد شده معتبر نیست. لطفاً «مرد» یا «زن» را وارد کنید:",
                buttons=back_to_main_button
            )
            return
        
        # تبدیل به فرمت استاندارد
        if gender in ["مرد", "مذکر", "آقا"]:
            standardized_gender = "مرد"
        else:
            standardized_gender = "زن"
        
        # ذخیره جنسیت در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "gender", standardized_gender)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_CITY)
        
        await event.respond(
            f"✅ جنسیت «{standardized_gender}» ثبت شد.\n\n"
            "لطفاً شهر محل سکونت شخص مورد نظر را وارد کنید:",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_CITY:
        # دریافت شهر
        city = text.strip()
        
        if not city:
            await event.respond(
                "❌ شهر وارد شده معتبر نیست. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # ذخیره شهر در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "city", city)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_JOB)
        
        await event.respond(
            f"✅ شهر «{city}» ثبت شد.\n\n"
            "لطفاً شغل یا حوزه فعالیت شخص مورد نظر را وارد کنید:",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_JOB:
        # دریافت شغل
        job = text.strip()
        
        if not job:
            await event.respond(
                "❌ شغل وارد شده معتبر نیست. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # ذخیره شغل در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "job", job)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_EVENT)
        
        await event.respond(
            f"✅ شغل «{job}» ثبت شد.\n\n"
            "لطفاً یک رویداد مهم یا نقطه عطف در زندگی شخص مورد نظر را وارد کنید (یا 'ندارم' بنویسید):",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_EVENT:
        # دریافت رویداد مهم
        event_info = text.strip()
        
        if not event_info:
            event_info = "اطلاعاتی در دسترس نیست"
        elif event_info.lower() == "ندارم":
            event_info = "اطلاعاتی در دسترس نیست"
        
        # ذخیره رویداد در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "notable_event", event_info)
        
        # تغییر وضعیت به مرحله بعدی
        user_manager.set_user_state(user_id, States.TYPING_RELATIONSHIP)
        
        await event.respond(
            f"✅ اطلاعات رویداد ثبت شد.\n\n"
            "لطفاً نوع رابطه یا هدف خود از تحلیل این پروفایل را وارد کنید (مثلاً: دوستی، کاری، عاطفی و...):",
            buttons=back_to_main_button
        )
    
    elif state == States.TYPING_RELATIONSHIP:
        # دریافت نوع رابطه
        relationship = text.strip()
        
        if not relationship:
            await event.respond(
                "❌ اطلاعات وارد شده معتبر نیست. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # ذخیره نوع رابطه در اطلاعات پروفایل
        user_manager.set_profile_info(user_id, "relationship", relationship)
        
        # دریافت تمام اطلاعات پروفایل
        profile_info = user_manager.get_profile_info(user_id)
        
        # نمایش خلاصه اطلاعات
        summary = (
            "📝 خلاصه اطلاعات وارد شده:\n\n"
            f"👤 نام کاربری: {profile_info.get('username', '')}\n"
            f"📋 نام: {profile_info.get('name', '')}\n"
            f"🎂 سال تولد: {profile_info.get('birth_year', '')}\n"
            f"👫 جنسیت: {profile_info.get('gender', '')}\n"
            f"🏙 شهر: {profile_info.get('city', '')}\n"
            f"💼 شغل: {profile_info.get('job', '')}\n"
            f"🔍 هدف تحلیل: {relationship}\n\n"
            "آیا اطلاعات فوق را تایید می‌کنید؟"
        )
        
        # دکمه‌های تایید یا ویرایش
        confirmation_buttons = [
            [Button.inline("✅ تأیید و شروع تحلیل", b"confirm_analysis")],
            [Button.inline("✏️ ویرایش اطلاعات", b"edit_profile_info")],
            back_to_main_button
        ]
        
        await event.respond(summary, buttons=confirmation_buttons)
    
    elif state == States.SEARCHING:
        # پردازش جستجو
        search_term = text.strip()
        
        if not search_term:
            await event.respond(
                "❌ عبارت جستجو نمی‌تواند خالی باشد. لطفاً مجدداً تلاش کنید:",
                buttons=back_to_main_button
            )
            return
        
        # در اینجا پردازش جستجو انجام می‌شود
        await event.respond(
            f"🔍 نتایج جستجو برای '{search_term}':\n\n"
            "نتیجه‌ای یافت نشد. لطفاً با عبارت دیگری جستجو کنید.",
            buttons=back_to_main_button
        )
    
    else:
        # اگر در هیچ حالت خاصی نیستیم، پیام را نادیده می‌گیریم
        pass

# -----------------------
# اجرای اصلی ربات
if __name__ == "__main__":
    try:
        # Register all event handlers
        logger.info("در حال ثبت هندلرهای رویدادها...")
        
        # Register message handler for UI messages
        ui_message_handler = events.NewMessage(func=ui_filter)
        bot.add_event_handler(ui_message_processor, ui_message_handler)
        
        # Import and register specialized handlers if needed
        if os.path.exists("src/handlers/message_handler.py") and os.path.exists("src/handlers/button_handler.py"):
            try:
                from handlers.message_handler import MessageHandler
                from handlers.button_handler import ButtonHandler
                
                # Create and register handlers
                message_handler = MessageHandler(bot, user_manager)
                button_handler = ButtonHandler(bot, user_manager)
                
                # Register handlers
                message_handler.register_handlers()
                button_handler.register_handlers()
                
                logger.info("هندلرهای تخصصی با موفقیت ثبت شدند")
            except Exception as handler_error:
                logger.error(f"خطا در ثبت هندلرهای تخصصی: {str(handler_error)}")
                traceback.print_exc()
        
        logger.info("ربات شروع به کار کرد.")
        bot.run_until_disconnected()
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {str(e)}")
        traceback.print_exc()

    # 2025-05-21 20:15:59,437 - __main__ - INFO - ربات شروع به کار کرد.