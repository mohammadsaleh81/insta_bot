from telethon import TelegramClient, events, Button
from telethon.tl.types import User as TelegramUser
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
def build_gpt_input(username, extra_info):
    try:
        profile_data = get_insta_data(username)
        posts_data = get_insta_posts(username)

        if not profile_data:
            raise Exception("خطا در دریافت اطلاعات پروفایل از اینستاگرام")
            
        if not posts_data:
            logger.warning(f"هشدار: اطلاعات پست‌های {username} دریافت نشد. ادامه با اطلاعات محدود.")

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
def get_personality_analysis(data_json):
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
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=[
                {"role": "user", "content": prompt}
            ],
            extra_body={},
            timeout=120  # زمان انتظار طولانی‌تر برای دریافت پاسخ
        )

        if not response or not response.choices or len(response.choices) == 0:
            raise Exception("پاسخی از API دریافت نشد")

        return response.choices[0].message.content
        
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
    user_states[user_id] = States.MAIN_MENU
    
    # بررسی اگر کاربر جدید است
    user_doc = users_collection.find_one({"user_id": user_id})
    is_new_user = not user_doc
    
    if is_new_user:
        # اضافه کردن سکه‌های رایگان اولیه برای کاربران جدید
        await update_user_coins(user_id, DEFAULT_COINS)
    
    # ذخیره اطلاعات کاربر در پایگاه داده
    await save_user_to_db(
        user_id, 
        sender.first_name, 
        sender.last_name if hasattr(sender, 'last_name') else None,
        sender.username if hasattr(sender, 'username') else None,
        sender.lang_code if hasattr(sender, 'lang_code') else None
    )
    
    # دریافت تعداد سکه‌های فعلی
    current_coins = await get_user_coins(user_id)
    
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
    
    try:
        # ارسال تصویر و منو
        await bot.send_file(
            event.chat_id,
            welcome_photo,
            caption=welcome_message,
            buttons=main_menu_buttons
        )
    except Exception as e:
        # اگر ارسال تصویر با خطا مواجه شد، فقط متن و منو را ارسال کن
        await event.respond(welcome_message, buttons=main_menu_buttons)

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
    user_states[user_id] = States.MAIN_MENU
    
    # پاک کردن اطلاعات کاربر اگر وجود داشت
    if user_id in user_profile_info:
        del user_profile_info[user_id]
    
    await event.respond(
        "عملیات لغو شد. به منوی اصلی بازگشتید.",
        buttons=main_menu_buttons
    )

# -----------------------
# رویداد دکمه‌ها
@bot.on(events.CallbackQuery())
async def button_callback(event):
    """پاسخ به کلیک روی دکمه‌ها"""
    sender = await event.get_sender()
    user_id = str(sender.id)
    data = event.data.decode('utf-8')
    
    # اگر کاربر در دیکشنری وضعیت‌ها نیست، او را به منوی اصلی هدایت کنید
    if user_id not in user_states:
        user_states[user_id] = States.MAIN_MENU
    
    state = user_states[user_id]
    
    if data == "back_to_main":
        user_states[user_id] = States.MAIN_MENU
        current_coins = await get_user_coins(user_id)
        await event.edit(
            f"به منوی اصلی بازگشتید.\n💰 سکه‌های شما: {current_coins}\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            buttons=main_menu_buttons
        )
    
    elif data == "start_analysis":
        # تنظیم وضعیت کاربر به حالت دریافت نام کاربری
        user_states[user_id] = States.TYPING_USERNAME
        
        # پاک کردن اطلاعات قبلی اگر وجود داشته باشد
        if user_id in user_profile_info:
            user_profile_info[user_id] = {}
            
        await event.edit(
            "👤 لطفاً نام کاربری اینستاگرام مورد نظر را وارد کنید:\n\n"
            "مثال: @username یا username\n\n"
            "⚠️ توجه: حساب کاربری باید عمومی (public) باشد.",
            buttons=back_to_main_button
        )
    
    elif data == "view_history":
        if user_id not in user_history or not user_history[user_id]:
            # تلاش برای بارگیری تاریخچه از پایگاه داده
            history_items = await load_user_history(user_id)
            
            if not history_items:
                await event.edit(
                    "📌 شما هنوز هیچ تحلیلی انجام نداده‌اید.\n\n"
                    "برای شروع، از گزینه 'تحلیل شخصیت' استفاده کنید.",
                    buttons=back_to_main_button
                )
                return
        else:
            history_items = user_history[user_id]
            
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
        current_coins = await get_user_coins(user_id)
        user_info = await get_user_info(user_id)
        
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
    
    elif data.startswith("buy_"):
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
# رویداد پیام‌های متنی
@bot.on(events.NewMessage(func=lambda e: e.text and not e.text.startswith('/')))
async def text_message_handler(event):
    """پردازش پیام‌های متنی"""
    user_id = str(event.sender_id)
    text = event.text.strip()
    
    # اگر کاربر در دیکشنری وضعیت‌ها نیست، او را به منوی اصلی هدایت کنید
    if user_id not in user_states:
        user_states[user_id] = States.MAIN_MENU
        await event.respond(
            "لطفاً از منوی اصلی شروع کنید:",
            buttons=main_menu_buttons
        )
        return
    
    state = user_states[user_id]
    
    # اگر کاربر در دیکشنری اطلاعات پروفایل نیست، یک پروفایل جدید ایجاد کنید
    if user_id not in user_profile_info:
        user_profile_info[user_id] = {}
    
    if state == States.TYPING_USERNAME:
        # حذف @ از ابتدای نام کاربری اگر وجود داشته باشد
        username = text.lstrip('@')
        user_profile_info[user_id]['username'] = username
        user_states[user_id] = States.TYPING_NAME
        await event.respond(
            f"نام کاربری ثبت شد: {username}\n\n"
            "لطفاً نام و نام خانوادگی را وارد کنید:"
        )
    
    elif state == States.TYPING_NAME:
        user_profile_info[user_id]['name'] = text
        user_states[user_id] = States.TYPING_BIRTH_YEAR
        await event.respond(
            f"نام ثبت شد: {text}\n\n"
            "لطفاً سال تولد را به صورت شمسی وارد کنید (مثال: 1370):"
        )
    
    elif state == States.TYPING_BIRTH_YEAR:
        try:
            birth_year = int(text)
            user_profile_info[user_id]['birth_year'] = birth_year
            
            # محاسبه سن بر اساس سال شمسی
            age = calculate_shamsi_age(birth_year)
            user_profile_info[user_id]['age_estimate'] = age
            
            user_states[user_id] = States.TYPING_GENDER
            await event.respond(
                f"سال تولد ثبت شد: {birth_year}\n"
                f"سن شما در سال 1404: {age} سال\n\n"
                "لطفاً جنسیت را وارد کنید:"
            )
        except ValueError:
            await event.respond("لطفاً یک عدد معتبر وارد کنید:")
    
    elif state == States.TYPING_GENDER:
        user_profile_info[user_id]['gender'] = text
        user_states[user_id] = States.TYPING_CITY
        await event.respond(
            f"جنسیت ثبت شد: {text}\n\n"
            "لطفاً شهر محل سکونت را وارد کنید:"
        )
    
    elif state == States.TYPING_CITY:
        user_profile_info[user_id]['city'] = text
        user_states[user_id] = States.TYPING_JOB
        await event.respond(
            f"شهر ثبت شد: {text}\n\n"
            "لطفاً شغل را وارد کنید:"
        )
    
    elif state == States.TYPING_JOB:
        user_profile_info[user_id]['job'] = text
        user_states[user_id] = States.TYPING_EVENT
        await event.respond(
            f"شغل ثبت شد: {text}\n\n"
            "لطفاً یک رویداد قابل توجه وارد کنید (مثال: جدایی، ازدواج، تغییر شغل):"
        )
    
    elif state == States.TYPING_EVENT:
        user_profile_info[user_id]['notable_event'] = text
        user_states[user_id] = States.MAIN_MENU
        
        # شروع فرایند تحلیل
        await start_analysis_process(event, user_id)
    
    elif state == States.CHATTING_WITH_AI:
        # بررسی موجودی سکه برای چت
        success, current_coins = await deduct_coins(user_id, CHAT_COST)
        if not success:
            await event.respond(
                f"⚠️ سکه‌های شما کافی نیست. موجودی فعلی: {current_coins} سکه\n"
                f"هر پیام چت {CHAT_COST} سکه هزینه دارد.\n"
                "لطفاً از بخش پروفایل کاربری، حساب خود را شارژ کنید.",
                buttons=main_menu_buttons
            )
            return
        
        try:
            # دریافت پاسخ از هوش مصنوعی
            response = await chat_with_ai(user_id, text)
            await event.respond(response)
        except Exception as e:
            logger.error(f"خطا در چت با هوش مصنوعی: {str(e)}")
            # برگرداندن سکه در صورت خطا
            await add_coins(user_id, CHAT_COST)
            await event.respond(
                "❌ متأسفانه در پردازش پیام خطایی رخ داد. لطفاً دوباره تلاش کنید.\n"
                "💰 سکه‌های شما برگردانده شد."
            )

# -----------------------
# فرایند تحلیل شخصیت
async def start_analysis_process(event, user_id):
    """شروع فرایند تحلیل شخصیت"""
    try:
        # بررسی موجودی سکه
        success, current_coins = await deduct_coins(user_id, ANALYSIS_COST)
        if not success:
            await event.respond(
                f"⚠️ سکه‌های شما کافی نیست. موجودی فعلی: {current_coins} سکه\n"
                f"هر تحلیل {ANALYSIS_COST} سکه هزینه دارد.\n"
                "لطفاً از بخش پروفایل کاربری، حساب خود را شارژ کنید.",
                buttons=main_menu_buttons
            )
            return
            
        profile_info = user_profile_info[user_id]
        if not profile_info:
            logger.error(f"خطا: اطلاعات پروفایل برای کاربر {user_id} یافت نشد")
            raise Exception("اطلاعات پروفایل یافت نشد")
            
        username = profile_info.get('username')
        if not username:
            logger.error(f"خطا: نام کاربری برای کاربر {user_id} یافت نشد")
            raise Exception("نام کاربری یافت نشد")
            
        logger.info(f"شروع تحلیل برای کاربر {username}")
        
        extra_info = {
            "name": profile_info.get('name', ''),
            "birth_year": profile_info.get('birth_year', 0),
            "age_estimate": profile_info.get('age_estimate', 0),
            "gender": profile_info.get('gender', ''),
            "city": profile_info.get('city', ''),
            "job": profile_info.get('job', ''),
            "notable_event": profile_info.get('notable_event', ''),
            "relationship": profile_info.get('relationship', '')
        }
        
        # ارسال پیام درحال پردازش
        processing_message = await event.respond("🔄 در حال دریافت اطلاعات از اینستاگرام...")
        
        try:
            logger.info("شروع ساخت داده‌های ورودی")
            data_json = build_gpt_input(username, extra_info)
            
            if not data_json:
                raise Exception("خطا در دریافت اطلاعات از اینستاگرام. لطفاً مطمئن شوید که:\n"
                              "1. نام کاربری را درست وارد کرده‌اید\n"
                              "2. حساب کاربری مورد نظر عمومی است\n"
                              "3. حساب کاربری مورد نظر وجود دارد")
            
            logger.info("داده‌های ورودی با موفقیت ساخته شد")
            
            await bot.edit_message(processing_message, "🧠 در حال تحلیل شخصیت با هوش مصنوعی...")
            
            logger.info("شروع دریافت تحلیل از API")
            analysis = get_personality_analysis(data_json)
            logger.info("تحلیل با موفقیت دریافت شد")
            
            # ذخیره تحلیل در تاریخچه کاربر و پایگاه داده
            await save_analysis_to_history(user_id, username, analysis)
            
            # ذخیره تحلیل برای استفاده در چت
            if 'current_analysis' not in user_profile_info[user_id]:
                user_profile_info[user_id]['current_analysis'] = {}
            user_profile_info[user_id]['current_analysis'] = {
                'username': username,
                'text': analysis,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # حذف پیام پردازش
            await bot.delete_messages(event.chat_id, processing_message)
            
            # ارسال نتیجه تحلیل به صورت چند پیام
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
            
            # نمایش گزینه‌های پایان تحلیل
            current_coins = await get_user_coins(user_id)
            buttons = [
                [Button.inline("💬 چت با هوش مصنوعی درباره این تحلیل", b"chat_with_ai")],
                [Button.inline("تحلیل جدید 🔄", b"start_analysis")],
                [Button.inline("بازگشت به منوی اصلی 🏠", b"back_to_main")]
            ]
            
            await event.respond(
                f"✅ تحلیل شخصیت با موفقیت انجام شد.\n"
                f"💰 سکه‌های باقیمانده: {current_coins}\n\n"
                "چه کاری می‌خواهید انجام دهید؟",
                buttons=buttons
            )
            
        except Exception as e:
            # در صورت خطا، سکه را برگردانیم
            await add_coins(user_id, ANALYSIS_COST)
            raise e
            
    except Exception as e:
        error_message = f"❌ خطا در تحلیل شخصیت: {str(e)}"
        logger.error(error_message)
        traceback.print_exc()
        
        # حذف پیام پردازش اگر وجود داشته باشد
        try:
            if 'processing_message' in locals():
                await bot.delete_messages(event.chat_id, processing_message)
        except:
            pass
        
        # برگرداندن سکه در صورت خطا
        await add_coins(user_id, ANALYSIS_COST)
        
        # نمایش پیام خطای مناسب به کاربر
        error_text = (
            "❌ متأسفانه در تحلیل شخصیت خطایی رخ داد.\n\n"
            "🔍 دلایل احتمالی:\n"
            "1. نام کاربری اشتباه وارد شده\n"
            "2. حساب کاربری خصوصی است\n"
            "3. حساب کاربری وجود ندارد\n"
            "4. مشکل در دسترسی به اینستاگرام\n\n"
            "💰 سکه‌های شما برگردانده شد.\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید: @InstaAnalysAiSupport"
        )
        
        await event.respond(error_text)
        
        # بازگشت به منوی اصلی
        buttons = [
            [Button.inline("تلاش مجدد 🔄", b"start_analysis")],
            [Button.inline("بازگشت به منوی اصلی 🏠", b"back_to_main")]
        ]
        
        await event.respond(
            "می‌خواهید چه کاری انجام دهید؟",
            buttons=buttons
        )

# -----------------------
# بازیابی تحلیل خاص از پایگاه داده
async def get_analysis_by_id(analysis_id):
    """بازیابی یک تحلیل خاص با شناسه آن از پایگاه داده"""
    try:
        analysis_doc = analysis_collection.find_one({"_id": ObjectId(analysis_id)})
        if analysis_doc:
            return analysis_doc
        return None
    except Exception as e:
        logger.error(f"خطا در بازیابی تحلیل با شناسه {analysis_id}: {str(e)}")
        return None

# -----------------------
# چت با هوش مصنوعی
async def chat_with_ai(user_id, message, analysis=None):
    """ارسال پیام به مدل هوش مصنوعی و دریافت پاسخ"""
    try:
        # بررسی موجودی سکه
        success, current_coins = await deduct_coins(user_id, CHAT_COST)
        if not success:
            return f"⚠️ سکه‌های شما کافی نیست. موجودی فعلی: {current_coins} سکه\n" \
                   f"هر پیام چت {CHAT_COST} سکه هزینه دارد.\n" \
                   "لطفاً از بخش پروفایل کاربری، حساب خود را شارژ کنید."
        
        # اگر تاریخچه چت برای این کاربر وجود ندارد، یک تاریخچه جدید ایجاد کنید
        if user_id not in user_chat_history:
            user_chat_history[user_id] = []
            
            # اگر تحلیل قبلی وجود دارد، آن را به عنوان اولین پیام سیستم اضافه کنید
            if analysis:
                user_chat_history[user_id].append({
                    "role": "system",
                    "content": f"شما یک مشاور شخصیت‌شناس هستید. شما قبلاً این تحلیل را درباره فرد مورد نظر ارائه کرده‌اید:\n\n{analysis}\n\nاکنون به سوالات کاربر در مورد این تحلیل پاسخ دهید. صمیمی و مفید باشید."
                })
            else:
                user_chat_history[user_id].append({
                    "role": "system",
                    "content": "شما یک مشاور شخصیت‌شناس هستید. به سوالات کاربر با صمیمیت و به صورت مفصل پاسخ دهید."
                })
                
        # افزودن پیام کاربر به تاریخچه
        user_chat_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        # محدود کردن تعداد پیام‌ها به ۲۰ پیام آخر برای جلوگیری از افزایش هزینه
        if len(user_chat_history[user_id]) > 21:  # ۱ پیام سیستم + ۲۰ پیام گفتگو
            user_chat_history[user_id] = [user_chat_history[user_id][0]] + user_chat_history[user_id][-20:]
            
        # ارسال درخواست به API
        logger.info("در حال ارسال درخواست چت به OpenAI API...")
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free",
            messages=user_chat_history[user_id],
            extra_body={},
            timeout=60
        )
        
        if not response or not response.choices or len(response.choices) == 0:
            # در صورت خطا، سکه را برگردانیم
            await add_coins(user_id, CHAT_COST)
            raise Exception("پاسخی از API دریافت نشد")
            
        reply = response.choices[0].message.content
        
        # افزودن پاسخ به تاریخچه
        user_chat_history[user_id].append({
            "role": "assistant",
            "content": reply
        })
        
        return reply
        
    except Exception as e:
        logger.error(f"خطا در چت با هوش مصنوعی: {str(e)}")
        traceback.print_exc()
        # در صورت خطا، سکه را برگردانیم
        await add_coins(user_id, CHAT_COST)
        return f"متأسفانه خطایی رخ داده است: {str(e)}"

# -----------------------
# اجرای اصلی ربات
if __name__ == "__main__":
    logger.info("ربات شروع به کار کرد.")
    bot.run_until_disconnected()

    # 2025-05-21 20:15:59,437 - __main__ - INFO - ربات شروع به کار کرد.