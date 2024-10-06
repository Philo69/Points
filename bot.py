from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

# Set your bot token and owner ID here
BOT_TOKEN = '7545754774:AAFLIaaJ8SSskfLsMZZsVEWFA0ZMcNd4DA0'
OWNER_ID = 7202072688  # Replace with your Telegram user ID (an integer)

async def start(update: Update, context) -> None:
    """Handle the /start command with a welcome message and image"""
    welcome_message = (
        "Welcome to Fʟᴀsʜ 🝮︎︎︎︎︎︎︎ Hᴜɴᴛᴇʀ!\n\n"
        "This bot is developed by [FlashShine](https://t.me/FlashShine)."
    )
    
    # Path to the image (update with the path where the image is stored)
    image_path = '/mnt/data/_830eec2b-cb51-4c5c-941a-e97b0151a3c5.jpeg'
    
    # Send the image
    with open(image_path, 'rb') as image:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(image), caption=welcome_message, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context) -> None:
    """Handle the /help command"""
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
    application.run_polling()

if __name__ == '__main__':
    main()
