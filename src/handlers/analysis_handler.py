import logging
from ..services.instagram_service import instagram_service
from ..services.ai_service import ai_service
from ..services.coin_service import coin_service
from ..utils.helpers import format_message_for_chunks
from ..config.settings import ANALYSIS_COST

logger = logging.getLogger(__name__)

class AnalysisHandler:
    def __init__(self, bot, user_manager):
        self.bot = bot
        self.user_manager = user_manager

    async def start_analysis_process(self, event, user):
        """Start the personality analysis process"""
        try:
            # Check coin balance
            success, current_coins = await coin_service.deduct_coins(user.user_id, ANALYSIS_COST)
            if not success:
                await event.respond(
                    f"⚠️ Not enough coins. Current balance: {current_coins} coins\n"
                    f"Each analysis costs {ANALYSIS_COST} coins.\n"
                    "Please charge your account from the user profile section.",
                    buttons=self.user_manager.main_menu_buttons
                )
                return
                
            profile_info = user.get_profile_info()
            if not profile_info:
                logger.error(f"Error: Profile info not found for user {user.user_id}")
                raise Exception("Profile information not found")
                
            username = profile_info.username
            if not username:
                logger.error(f"Error: Username not found for user {user.user_id}")
                raise Exception("Username not found")
                
            logger.info(f"Starting analysis for user {username}")
            
            # Send processing message
            processing_message = await event.respond("🔄 Getting information from Instagram...")
            
            try:
                logger.info("Starting input data build")
                data_json = instagram_service.build_gpt_input(username, profile_info.__dict__)
                
                if not data_json:
                    raise Exception("Error getting information from Instagram. Please make sure:\n"
                                  "1. You entered the correct username\n"
                                  "2. The account is public\n"
                                  "3. The account exists")
                
                logger.info("Input data built successfully")
                
                await self.bot.edit_message(processing_message, "🧠 Analyzing personality with AI...")
                
                logger.info("Starting analysis from API")
                analysis = ai_service.get_personality_analysis(data_json)
                logger.info("Analysis received successfully")
                
                # Save analysis to user history and database
                await self.user_manager.save_analysis(user.user_id, username, analysis)
                
                # Save analysis for chat use
                user.set_current_analysis({
                    'username': username,
                    'text': analysis,
                    'timestamp': self.user_manager.get_current_timestamp()
                })
                
                # Delete processing message
                await self.bot.delete_messages(event.chat_id, processing_message)
                
                # Send analysis result in chunks
                chunks = format_message_for_chunks(analysis)
                for chunk in chunks:
                    await event.respond(chunk)
                
                # Show end of analysis options
                current_coins = await coin_service.get_user_coins(user.user_id)
                buttons = [
                    [Button.inline("💬 Chat with AI about this analysis", b"chat_with_ai")],
                    [Button.inline("New Analysis 🔄", b"start_analysis")],
                    [Button.inline("Back to Main Menu 🏠", b"back_to_main")]
                ]
                
                await event.respond(
                    f"✅ Personality analysis completed successfully.\n"
                    f"💰 Remaining coins: {current_coins}\n\n"
                    "What would you like to do?",
                    buttons=buttons
                )
                
            except Exception as e:
                # Refund coins on error
                await coin_service.add_coins(user.user_id, ANALYSIS_COST)
                raise e
                
        except Exception as e:
            error_message = f"❌ Error in personality analysis: {str(e)}"
            logger.error(error_message)
            
            # Delete processing message if it exists
            try:
                if 'processing_message' in locals():
                    await self.bot.delete_messages(event.chat_id, processing_message)
            except:
                pass
            
            # Refund coins on error
            await coin_service.add_coins(user.user_id, ANALYSIS_COST)
            
            # Show appropriate error message to user
            error_text = (
                "❌ An error occurred during personality analysis.\n\n"
                "🔍 Possible reasons:\n"
                "1. Incorrect username\n"
                "2. Private account\n"
                "3. Account doesn't exist\n"
                "4. Instagram access problem\n\n"
                "💰 Your coins have been refunded.\n"
                "Please try again or contact support: @InstaAnalysAiSupport"
            )
            
            await event.respond(error_text)
            
            # Return to main menu
            buttons = [
                [Button.inline("Try Again 🔄", b"start_analysis")],
                [Button.inline("Back to Main Menu 🏠", b"back_to_main")]
            ]
            
            await event.respond(
                "What would you like to do?",
                buttons=buttons
            ) 