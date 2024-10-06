import random
import string
import requests
import re
import aiosqlite
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Set up logging to debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # This will print debug messages
)

# Define the bot owner's user ID and bot token
BOT_OWNER_ID = 7202072688  # Replace with your actual Telegram user ID
BOT_TOKEN = "7779270006:AAHQYNzVIcytbmeMkkxyp4DtXqzIY8BGsWE"  # Replace this with your actual bot token

# Function to generate random keys
def generate_random_key(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Database handling using async context managers
async def get_db_connection():
    conn = await aiosqlite.connect('points.db')
    await conn.execute('''CREATE TABLE IF NOT EXISTS user_points
                          (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER, custom_title TEXT, credits INTEGER DEFAULT 0, premium INTEGER DEFAULT 0)''')
    await conn.execute('''CREATE TABLE IF NOT EXISTS redemption_keys
                          (key TEXT PRIMARY KEY, user_id INTEGER, credits INTEGER, redeemed INTEGER DEFAULT 0)''')
    return conn

# /start command with a short welcome message
async def start_command(update: Update, context: CallbackContext) -> None:
    logging.info(f"Received /start command from {update.message.from_user.username}")
    await update.message.reply_text(
        "🎉 Welcome to Good Charged Bot! 🎉\n\n"
        "Use /help to explore all the available commands."
    )

# /help command showing all commands
async def help_command(update: Update, context: CallbackContext) -> None:
    logging.info(f"Received /help command from {update.message.from_user.username}")
    help_message = (
        "<b>Available Commands:</b>\n\n"
        "• /start - Show a welcome message\n"
        "• /help - Show this help message\n"
        "• /redeem <key> - Redeem a key to become premium and receive credits\n"
        "• /generatekey <user_id> <credits> <number_of_codes> - (Owner Only) Generate multiple redemption keys\n"
        "• /gateway <url> - Check if a website uses 2D or 3D Stripe payments\n"
    )
    await update.message.reply_text(help_message, parse_mode="HTML")

# Catch-all message handler to ensure the bot receives messages
async def handle_message(update: Update, context: CallbackContext):
    logging.info(f"Received a message: {update.message.text}")
    await update.message.reply_text(f"Echo: {update.message.text}")

# Initialize the bot application and run it
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Message handler to catch all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Bot is starting...")

    # Start polling for updates
    await application.initialize()
    await application.start()
    await application.run_polling()  # Corrected to run_polling
    
    # Idle to keep the bot running
    await application.idle()

# Running the bot inside the current event loop without asyncio.run()
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
