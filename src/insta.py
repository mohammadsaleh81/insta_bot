import requests
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
RAPIDAPI_HOST = "instagram230.p.rapidapi.com"

def get_insta_data(username):
    """
    Get Instagram profile data for a given username.
    
    Args:
        username (str): Instagram username
        
    Returns:
        dict or None: JSON response data or None if error
    """
    url = f"https://{RAPIDAPI_HOST}/user/details"

    querystring = {"username": username}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    try:
        logger.info(f"درخواست اطلاعات پروفایل برای {username}")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.error(f"داده‌ای از API برای {username} دریافت نشد")
            return None
            
        if 'status' in data and data['status'] != 'ok':
            logger.error(f"خطا در پاسخ API برای {username}: {data.get('message', 'خطای نامشخص')}")
            return None
            
        logger.info(f"اطلاعات پروفایل {username} با موفقیت دریافت شد")
        logger.debug(f"پاسخ API پروفایل: {data}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"تایم‌اوت در دریافت اطلاعات پروفایل برای {username}")
        return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"خطای HTTP در دریافت اطلاعات پروفایل برای {username}: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"خطای درخواست در دریافت اطلاعات پروفایل برای {username}: {req_err}")
        return None
    except ValueError as json_err:
        logger.error(f"خطای پردازش JSON در دریافت اطلاعات پروفایل برای {username}: {json_err}")
        return None
    except Exception as e:
        logger.error(f"خطای نامشخص در get_insta_data: {str(e)}")
        return None


def get_insta_posts(username):
    """
    Get Instagram posts data for a given username.
    
    Args:
        username (str): Instagram username
        
    Returns:
        dict or None: JSON response data or None if error
    """
    url = f"https://{RAPIDAPI_HOST}/user/posts"

    querystring = {"username": username}

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        logger.info(f"درخواست اطلاعات پست‌ها برای {username}")
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.error(f"داده‌ای از API پست‌ها برای {username} دریافت نشد")
            return None
            
        if 'status' in data and data['status'] != 'ok':
            logger.error(f"خطا در پاسخ API پست‌ها برای {username}: {data.get('message', 'خطای نامشخص')}")
            return None
            
        logger.info(f"اطلاعات پست‌های {username} با موفقیت دریافت شد")
        logger.debug(f"پاسخ API پست‌ها: {data}")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"تایم‌اوت در دریافت اطلاعات پست‌ها برای {username}")
        return None
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"خطای HTTP در دریافت اطلاعات پست‌ها برای {username}: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"خطای درخواست در دریافت اطلاعات پست‌ها برای {username}: {req_err}")
        return None
    except ValueError as json_err:
        logger.error(f"خطای پردازش JSON در دریافت اطلاعات پست‌ها برای {username}: {json_err}")
        return None
    except Exception as e:
        logger.error(f"خطای نامشخص در get_insta_posts: {str(e)}")
        return None
