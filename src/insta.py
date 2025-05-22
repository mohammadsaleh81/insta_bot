import aiohttp
import time
import logging
import os
from dotenv import load_dotenv

# بارگیری متغیرهای محیطی
load_dotenv()

# تنظیمات لاگینگ
logger = logging.getLogger(__name__)

# دریافت کلید API از متغیرهای محیطی
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "starapi1.p.rapidapi.com"

async def get_insta_data(username):
    """
    Get Instagram profile data for a given username.
    
    Args:
        username (str): Instagram username
        
    Returns:
        dict or None: JSON response data or None if error
    """
    url = f"https://{RAPIDAPI_HOST}/instagram/user/get_web_profile_info"

    payload = {"username": username}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    try:
        logger.info(f"درخواست اطلاعات پروفایل برای {username}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"خطای HTTP در دریافت اطلاعات پروفایل برای {username}: {response.status}")
                    return None
                    
                data = await response.json()
        
        if not data:
            logger.error(f"داده‌ای از API برای {username} دریافت نشد")
            return None
            
        if data.get('status') != 'done' or 'response' not in data:
            logger.error(f"خطا در پاسخ API برای {username}: {data.get('message', 'خطای نامشخص')}")
            return None
            
        logger.info(f"اطلاعات پروفایل {username} با موفقیت دریافت شد")
        logger.debug(f"پاسخ API پروفایل: {data}")
        return data['response']['body']
        
    except aiohttp.ClientTimeout:
        logger.error(f"تایم‌اوت در دریافت اطلاعات پروفایل برای {username}")
        return None
    except aiohttp.ClientError as http_err:
        logger.error(f"خطای HTTP در دریافت اطلاعات پروفایل برای {username}: {http_err}")
        return None
    except ValueError as json_err:
        logger.error(f"خطای پردازش JSON در دریافت اطلاعات پروفایل برای {username}: {json_err}")
        return None
    except Exception as e:
        logger.error(f"خطای نامشخص در get_insta_data: {str(e)}")
        return None


async def get_insta_posts(username, count=5):
    """
    Get Instagram posts data for a given username.
    
    Args:
        username (str): Instagram username
        count (int): Number of posts to retrieve (default: 5)
        
    Returns:
        dict or None: JSON response data or None if error
    """
    # اول باید شناسه کاربر را از طریق اطلاعات پروفایل دریافت کنیم
    profile_data = await get_insta_data(username)
    if not profile_data or 'data' not in profile_data or 'user' not in profile_data['data']:
        logger.error(f"نمی‌توان شناسه کاربر را برای {username} پیدا کرد")
        return None
        
    user_id = profile_data['data']['user'].get('id')
    if not user_id:
        logger.error(f"شناسه کاربر برای {username} یافت نشد")
        return None

    url = f"https://{RAPIDAPI_HOST}/instagram/user/get_media"

    payload = {
        "id": user_id,
        "count": count
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"درخواست اطلاعات پست‌ها برای {username} با شناسه {user_id}")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"خطای HTTP در دریافت اطلاعات پست‌ها برای {username}: {response.status}")
                    return None
                    
                data = await response.json()
        
        if not data:
            logger.error(f"داده‌ای از API پست‌ها برای {username} دریافت نشد")
            return None
            
        if data.get('status') != 'done' or 'response' not in data:
            logger.error(f"خطا در پاسخ API پست‌ها برای {username}: {data.get('message', 'خطای نامشخص')}")
            return None
            
        logger.info(f"اطلاعات پست‌های {username} با موفقیت دریافت شد")
        logger.debug(f"پاسخ API پست‌ها: {data}")
        return data['response']['body']
        
    except aiohttp.ClientTimeout:
        logger.error(f"تایم‌اوت در دریافت اطلاعات پست‌ها برای {username}")
        return None
    except aiohttp.ClientError as http_err:
        logger.error(f"خطای HTTP در دریافت اطلاعات پست‌ها برای {username}: {http_err}")
        return None
    except ValueError as json_err:
        logger.error(f"خطای پردازش JSON در دریافت اطلاعات پست‌ها برای {username}: {json_err}")
        return None
    except Exception as e:
        logger.error(f"خطای نامشخص در get_insta_posts: {str(e)}")
        return None
