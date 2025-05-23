from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..models.user import UserRole
from ..database.mongodb import db
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin panel"""
    user_id = update.effective_user.id
    user_doc = await db.users_collection.find_one({"user_id": str(user_id)})
    
    if not user_doc or user_doc.get("role") != UserRole.ADMIN.value:
        await update.message.reply_text("⛔️ شما دسترسی به پنل ادمین ندارید.")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users"),
            InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🚫 کاربران مسدود", callback_data="admin_blocked"),
            InlineKeyboardButton("💰 مدیریت سکه", callback_data="admin_coins")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔐 پنل مدیریت:", reply_markup=reply_markup)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    user_id = update.effective_user.id
    user_doc = await db.users_collection.find_one({"user_id": str(user_id)})
    
    if not user_doc or user_doc.get("role") != UserRole.ADMIN.value:
        await query.answer("⛔️ شما دسترسی به پنل ادمین ندارید.", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == "admin_users":
        users = await db.get_all_users(limit=10)
        message = "👥 لیست کاربران:\n\n"
        for user in users:
            message += f"🆔 {user['user_id']}\n"
            message += f"👤 {user.get('first_name', '')} {user.get('last_name', '')}\n"
            message += f"📊 تعداد آنالیز: {user.get('analysis_count', 0)}\n"
            message += f"💰 سکه: {user.get('coins', 0)}\n"
            message += f"⏰ آخرین فعالیت: {user.get('last_activity', 'نامشخص')}\n"
            message += "➖➖➖➖➖➖➖➖\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == "admin_stats":
        stats = await db.get_system_analytics()
        if not stats:
            await query.edit_message_text("❌ خطا در دریافت آمار سیستم")
            return
            
        message = "📊 آمار سیستم:\n\n"
        message += f"👥 تعداد کل کاربران: {stats['total_users']}\n"
        message += f"📈 تعداد کل آنالیزها: {stats['total_analyses']}\n"
        message += f"👤 کاربران فعال 24 ساعت گذشته: {stats['active_users_24h']}\n\n"
        message += "📊 آخرین آنالیزها:\n"
        
        for analysis in stats['recent_analyses'][:5]:
            message += f"👤 {analysis.get('username', 'نامشخص')}\n"
            message += f"⏰ {analysis.get('timestamp', 'نامشخص')}\n"
            message += "➖➖➖➖➖➖➖➖\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == "admin_blocked":
        blocked_users = list(await db.blocked_users_collection.find().limit(10))
        message = "🚫 کاربران مسدود شده:\n\n"
        
        if not blocked_users:
            message += "هیچ کاربری مسدود نشده است."
        else:
            for user in blocked_users:
                user_info = await db.users_collection.find_one({"user_id": user["user_id"]})
                if user_info:
                    message += f"🆔 {user['user_id']}\n"
                    message += f"👤 {user_info.get('first_name', '')} {user_info.get('last_name', '')}\n"
                    message += f"⏰ تاریخ مسدودی: {user.get('blocked_at', 'نامشخص')}\n"
                    message += f"📝 دلیل: {user.get('reason', 'نامشخص')}\n"
                    message += "➖➖➖➖➖➖➖➖\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    
    elif query.data == "admin_coins":
        keyboard = [
            [InlineKeyboardButton("➕ افزایش سکه", callback_data="admin_add_coins")],
            [InlineKeyboardButton("➖ کاهش سکه", callback_data="admin_remove_coins")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💰 مدیریت سکه های کاربران:", reply_markup=reply_markup)
    
    elif query.data == "admin_back":
        keyboard = [
            [
                InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users"),
                InlineKeyboardButton("📊 آمار سیستم", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("🚫 کاربران مسدود", callback_data="admin_blocked"),
                InlineKeyboardButton("💰 مدیریت سکه", callback_data="admin_coins")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔐 پنل مدیریت:", reply_markup=reply_markup)

async def block_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /block command to block a user"""
    user_id = update.effective_user.id
    user_doc = await db.users_collection.find_one({"user_id": str(user_id)})
    
    if not user_doc or user_doc.get("role") != UserRole.ADMIN.value:
        await update.message.reply_text("⛔️ شما دسترسی به این دستور را ندارید.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ لطفا آیدی کاربر را وارد کنید.\nمثال: /block 123456789 دلیل مسدودی")
        return
    
    target_user_id = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
    
    if await db.block_user(target_user_id, reason):
        await update.message.reply_text(f"✅ کاربر {target_user_id} با موفقیت مسدود شد.")
    else:
        await update.message.reply_text("❌ خطا در مسدود کردن کاربر.")

async def unblock_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unblock command to unblock a user"""
    user_id = update.effective_user.id
    user_doc = await db.users_collection.find_one({"user_id": str(user_id)})
    
    if not user_doc or user_doc.get("role") != UserRole.ADMIN.value:
        await update.message.reply_text("⛔️ شما دسترسی به این دستور را ندارید.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ لطفا آیدی کاربر را وارد کنید.\nمثال: /unblock 123456789")
        return
    
    target_user_id = context.args[0]
    
    if await db.unblock_user(target_user_id):
        await update.message.reply_text(f"✅ کاربر {target_user_id} با موفقیت از مسدودی خارج شد.")
    else:
        await update.message.reply_text("❌ خطا در خارج کردن کاربر از مسدودی.") 