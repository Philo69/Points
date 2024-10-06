import logging
import os
import requests
from telegram import Update, InputFile
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

# Path to store the downloaded image locally
local_image_path = 'cached_image.jpg'
image_url = 'https://files.catbox.moe/okjpvp.jpg'

def download_image(url, path):
    """Download the image from the URL and save it locally."""
    if not os.path.exists(path):
        logger.info(f"Downloading image from {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
            logger.info("Image downloaded and saved locally.")
        else:
            logger.error(f"Failed to download image: {response.status_code}")
    else:
        logger.info("Image already cached locally.")

async def start(update: Update, context) -> None:
    """Handle the /start command with a welcome message and image"""
    welcome_message = (
        "Welcome to Fʟᴀsʜ 🝮︎︎︎︎︎︎︎ Hᴜɴᴛᴇʀ!\n\n"
        "This bot is developed by [FlashShine](https://t.me/FlashShine)."
    )

    # Send the pre-downloaded image from the local file
    if os.path.exists(local_image_path):
        with open(local_image_path, 'rb') as image:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(image), caption=welcome_message, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Error: Image not found.")

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
    # Preload the image by downloading it once
    download_image(image_url, local_image_path)

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
