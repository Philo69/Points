import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import logging

# Set up logging to monitor the bot's behavior
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Set to DEBUG to get more detailed logs
)

# Connect to or create the database
conn = sqlite3.connect('points.db')
c = conn.cursor()

# Create table to store user points if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS user_points
             (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER)''')
conn.commit()

# Function to add points to a user
def add_point(user_id, username):
    c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
    result = c.fetchone()

    if result is None:
        # If user not in DB, add them
        c.execute("INSERT INTO user_points (user_id, username, points) VALUES (?, ?, ?)", 
                  (user_id, username, 1))
    else:
        # Update points for existing user
        current_points = result[0]
        c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", 
                  (current_points + 1, user_id))
    conn.commit()

# Function to get a user's points
def get_points(user_id):
    c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
    result = c.fetchone()
    if result is None:
        return 0
    return result[0]

# Inline keyboard with "Developer" and "Points" buttons
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Developer", url="https://t.me/TechPiro"),  # Link to your Telegram ID
            InlineKeyboardButton("Points", callback_data="points")  # Inline button for points
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command with welcome message and inline buttons
async def start(update: Update, context: CallbackContext) -> None:
    logging.info(f"Received /start command from user: {update.message.from_user.id}")
    
    welcome_message = (
        "👋 Welcome to the Points Bot!\n\n"
        "You can give points to users by replying with the word 'Pro' to their messages.\n\n"
        "Use the buttons below to see your points or learn more about the developer."
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_keyboard()  # Show inline buttons
    )

# Points command to check user's points
async def points_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    points = get_points(user_id)
    logging.info(f"Sending points to user: {username} ({user_id})")
    await update.message.reply_text(f'{username}, you have {points} points.')

# Handle callback queries from inline buttons (like "Points" button)
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "points":
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        points = get_points(user_id)
        logging.info(f"Points button clicked by user: {username} ({user_id})")
        await query.edit_message_text(f'{username}, you have {points} points.')

# Function to handle messages and give points
async def handle_message(update: Update, context: CallbackContext) -> None:
    logging.info(f"Received message: {update.message.text} from user: {update.message.from_user.id}")
    message_text = update.message.text
    if "Pro" in message_text and update.message.reply_to_message:
        original_message_user = update.message.reply_to_message.from_user
        user_id = original_message_user.id
        username = original_message_user.username or original_message_user.first_name
        
        add_point(user_id, username)
        points = get_points(user_id)
        logging.info(f"{username} got +1 Point. Total points: {points}")
        await update.message.reply_text(f'{username} got +1 Point ⭐! Total points: {points}')

# Welcome new members
async def welcome(update: Update, context: CallbackContext):
    new_members = update.message.new_chat_members
    for member in new_members:
        logging.info(f"New member joined: {member.full_name}")
        await update.message.reply_text(f"Welcome {member.full_name}! 🎉")

# Log all updates to troubleshoot
async def log_updates(update: Update, context: CallbackContext):
    logging.info(f"Received update: {update}")

# Main function to start the bot
async def main():
    # Replace 'YOUR_TOKEN' with your actual Telegram bot token
    application = Application.builder().token("7913432029:AAF0I1TWqzIqhz5Gv19xV_2JcW0YYkzaX5Q").build()

    # Register command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Register command handler for /points
    application.add_handler(CommandHandler("points", points_command))

    # Register callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register message handler to catch text messages and award points
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Register welcome message handler when new members join
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    # Log updates for troubleshooting
    application.add_handler(MessageHandler(filters.ALL, log_updates))

    # Log startup message
    logging.info("Bot started successfully.")
    
    # Run the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

# Check if there's an existing event loop running
if __name__ == '__main__':
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task for the bot
            loop.create_task(main())
        else:
            # If no loop is running, run the bot normally
            asyncio.run(main())
    except RuntimeError:
        # In case no event loop is found, start a new one
        asyncio.run(main())
