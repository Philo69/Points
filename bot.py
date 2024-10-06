import logging
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Set your bot token and owner ID here
BOT_TOKEN = '7545754774:AAFLIaaJ8SSskfLsMZZsVEWFA0ZMcNd4DA0'
OWNER_ID = 7202072688  # Replace with your Telegram user ID (an integer)

async def start(update: Update, context) -> None:
    """Handle the /start command with a welcome message and image"""
    logger.info(f"/start command received from user: {update.effective_user.id}")
    welcome_message = (
        "Welcome to Fʟᴀsʜ 🝮︎︎︎︎︎︎︎ Hᴜɴᴛᴇʀ!\n\n"
        "This bot is developed by [FlashShine](https://t.me/FlashShine)."
    )
    
    # URL of the image
    image_url = 'https://files.catbox.moe/okjpvp.jpg'
    
    # Send the image from the URL
    try:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=welcome_message, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Image and message sent successfully to user: {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Failed to send image or message: {str(e)}")

async def help_command(update: Update, context) -> None:
    """Handle the /help command"""
    logger.info(f"/help command received from user: {update.effective_user.id}")
    help_message = (
        "🝮︎︎︎︎︎︎︎ Help Menu 🝮︎︎︎︎︎︎︎\n\n"
        "Use /start to get the welcome message and bot details.\n"
        "Use /help to display this help message."
    )
    await update.message.reply_text(help_message)

def main():
    """Start the bot"""
    # Create the application with the bot token
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Start the bot with polling
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
