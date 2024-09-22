import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

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
        c.execute("INSERT INTO user_points (user_id, username, points) VALUES (?, ?, ?)", 
                  (user_id, username, 1))
    else:
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
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Reply with "Pro" to give points to the user you are replying to!')

# Points command to check user's points
def points(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name
    
    points = get_points(user_id)
    update.message.reply_text(f'{username}, you have {points} points.')

# Function to handle messages
def handle_message(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    
    if "Pro" in message_text and update.message.reply_to_message:
        original_message_user = update.message.reply_to_message.from_user
        user_id = original_message_user.id
        username = original_message_user.username or original_message_user.first_name
        
        add_point(user_id, username)
        points = get_points(user_id)
        update.message.reply_text(f'{username} got +1 Point ⭐! Total points: {points}')

def main():
    updater = Updater("7913432029:AAF0I1TWqzIqhz5Gv19xV_2JcW0YYkzaX5Q", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("points", points))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
