from telegram import Update, ParseMode, InputFile
from telegram.ext import Updater, CommandHandler, CallbackContext

# Set your bot token and owner ID here
BOT_TOKEN = '7545754774:AAFLIaaJ8SSskfLsMZZsVEWFA0ZMcNd4DA0'
OWNER_ID = 7202072688  # Replace with your Telegram user ID (an integer)

def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command with a welcome message and image"""
    welcome_message = (
        "Welcome to Fʟᴀsʜ 🝮︎︎︎︎︎︎︎ Hᴜɴᴛᴇʀ!\n\n"
        "This bot is developed by [FlashShine](https://t.me/FlashShine)."
    )
    
    # Path to the image (update with the path where the image is stored)
    image_path = '/mnt/data/_830eec2b-cb51-4c5c-941a-e97b0151a3c5.jpeg'
    
    # Send the image
    with open(image_path, 'rb') as image:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(image), caption=welcome_message, parse_mode=ParseMode.MARKDOWN)

def help_command(update: Update, context: CallbackContext) -> None:
    """Handle the /help command"""
    help_message = (
        "🝮︎︎︎︎︎︎︎ Help Menu 🝮︎︎︎︎︎︎︎\n\n"
        "Use /start to get the welcome message and bot details.\n"
        "Use /help to display this help message."
    )
    update.message.reply_text(help_message)

def main():
    """Start the bot"""
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
