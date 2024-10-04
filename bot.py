import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import logging
from telegram.helpers import mention_html  # Import for user mentions
import os
import asyncio

# Set up logging to monitor the bot's behavior
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Database handling with context managers to prevent locks
def get_db_connection():
    conn = sqlite3.connect('points.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS user_points
                 (user_id INTEGER PRIMARY KEY, username TEXT, points INTEGER)''')
    return conn

# Function to add points to a user
def add_point(user_id, username):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
        result = c.fetchone()

        if result is None:
            c.execute("INSERT INTO user_points (user_id, username, points) VALUES (?, ?, ?)", 
                      (user_id, username, 1))
        else:
            current_points = result[0]
            c.execute("UPDATE user_points SET points = ? WHERE user_id = ?", 
                      (current_points + 1, user_id))
        conn.commit()

# Function to get a user's points
def get_points(user_id):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT points FROM user_points WHERE user_id=?", (user_id,))
        result = c.fetchone()
        if result is None:
            return 0
        return result[0]

# Function to get a title based on points
def get_user_title(points):
    if points <= 10:
        return "Novice"
    elif points <= 50:
        return "Pro"
    elif points <= 100:
        return "Champion"
    else:
        return "Legend"

# Function to get top users by points
def get_top_users(limit=10):
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, username, points FROM user_points ORDER BY points DESC LIMIT ?", (limit,))
        return c.fetchall()

# Inline keyboard with "Developer" and "Points" buttons
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("Developer", url="https://t.me/TechPiro"),
            InlineKeyboardButton("Points", callback_data="points")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Start command with an attractive message
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "👋 <b>Welcome to the Points Bot!</b>\n\n"
        "🏅 Earn points by interacting with the bot!\n\n"
        "✨ You can give points by replying with the word 'Pro' to other users' messages. "
        "The more points you earn, the higher your title!\n\n"
        "Use the buttons below to check your points or learn more about the developer."
    )
    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard(), parse_mode="HTML")

# Help command
async def help_command(update: Update, context: CallbackContext) -> None:
    help_message = (
        "<b>How to use Points Bot</b>\n\n"
        "🎯 <b>Commands:</b>\n"
        "/start - Show the welcome message\n"
        "/points - Check your current points\n"
        "/top - See the top 10 users with the highest points\n"
        "/profile - View your profile with your points and title\n\n"
        "🏅 <b>Points System:</b>\n"
        "Reply with the word 'Pro' to give points to other users. The more points you earn, the higher your title!"
    )
    await update.message.reply_text(help_message, parse_mode="HTML")

# Points command
async def points_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    points = get_points(user_id)
    await update.message.reply_text(f'{username}, you have {points} points.')

# Profile command to show user profile and title
async def profile_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    points = get_points(user_id)
    title = get_user_title(points)
    
    profile_message = (
        f"👤 <b>Profile</b>\n\n"
        f"🧑‍💻 <b>Username:</b> {mention_html(user_id, username)}\n"
        f"🏅 <b>Points:</b> {points}\n"
        f"🎖 <b>Title:</b> {title}"
    )
    await update.message.reply_text(profile_message, parse_mode="HTML")

# Top users command to display leaderboard
async def top_command(update: Update, context: CallbackContext) -> None:
    top_users = get_top_users(limit=10)
    
    if not top_users:
        await update.message.reply_text("No users with points yet!")
        return
    
    leaderboard = "🏆 <b>Top 10 Users by Points</b> 🏆\n\n"
    for i, (user_id, username, points) in enumerate(top_users, start=1):
        mention = mention_html(user_id, username)
        leaderboard += f"{i}. {mention} — {points} points\n"

    await update.message.reply_text(leaderboard, parse_mode="HTML")

# Handle callback queries
async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "points":
        user_id = query.from_user.id
        username = query.from_user.username or query.from_user.first_name
        points = get_points(user_id)
        await query.edit_message_text(f'{username}, you have {points} points.')

# Handle messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    if "Pro" in message_text and update.message.reply_to_message:
        original_message_user = update.message.reply_to_message.from_user
        user_id = original_message_user.id
        username = original_message_user.username or original_message_user.first_name
        
        add_point(user_id, username)
        points = get_points(user_id)
        await update.message.reply_text(f'{username} got +1 Point ⭐! Total points: {points}')

# Welcome new members
async def welcome(update: Update, context: CallbackContext):
    new_members = update.message.new_chat_members
    for member in new_members:
        await update.message.reply_text(f"Welcome {member.full_name}! 🎉")

# Log all updates
async def log_updates(update: Update, context: CallbackContext):
    logging.info(f"Received update: {update}")

# Main function to start the bot
async def main():
    # Using environment variable for bot token
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        raise ValueError("No Bot Token provided!")

    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))  # Add help command
    application.add_handler(CommandHandler("points", points_command))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("profile", profile_command))  # Add profile command
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.ALL, log_updates))

    # Ensure that polling runs correctly, and handle cancellations gracefully
    logging.info("Bot started successfully.")
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        await application.updater.idle()
    except asyncio.CancelledError:
        logging.error("Polling cancelled. Exiting.")

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            asyncio.run(main())
    except RuntimeError:
        asyncio.run(main())
