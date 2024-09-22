import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging

# Set up logging to log issues and errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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

# Start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hi! Reply with "Pro" to give points to the user you are replying to!')

# Points command to check user's points
async def points(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    points = get_points(user_id)
    await update.message.reply_text(f'{username}, you have {points} points.')

# Function to handle messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    
    if "Pro" in message_text and update.message.reply_to_message:
        original_message_user = update.message.reply_to_message.from_user
        user_id = original_message_user.id
        username = original_message_user.username or original_message_user.first_name
        
        add_point(user_id, username)
        points = get_points(user_id)
        await update.message.reply_text(f'{username} got +1 Point ⭐! Total points: {points}')

# Main function to start the bot
async def main():
    # Replace 'YOUR_TOKEN' with your actual Telegram bot token
    application = Application.builder().token("7913432029:AAF0I1TWqzIqhz5Gv19xV_2JcW0YYkzaX5Q").build()

    # Register command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Register command handler for /points
    application.add_handler(CommandHandler("points", points))

    # Register message handler to catch text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Log startup message
    logging.info("Bot started successfully.")
    
    # Run the bot using the current running event loop
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        await application.updater.idle()
    except asyncio.CancelledError:
        logging.info("Polling was cancelled, shutting down gracefully.")

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
