import telebot
import random
from pymongo import MongoClient, errors
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import schedule
import time

# Replace with your actual bot API token and Telegram channel ID
API_TOKEN = "7825167784:AAFgZLZZeyWk3aItTYL2U9LiQ1sbxFQFadA"
BOT_OWNER_ID = 7222795580  # Replace with the owner’s Telegram ID
CHANNEL_ID = -1002438449944  # Replace with your Telegram channel ID where characters are logged

# MongoDB Connection
try:
    MONGO_URI = "mongodb+srv://PhiloWise:Philo@waifu.yl9tohm.mongodb.net/?retryWrites=true&w=majority&appName=Waifu"
    client = MongoClient(MONGO_URI)
    db = client['philo_grabber']  # Database name
    users_collection = db['users']  # Collection for user data
    characters_collection = db['characters']  # Collection for character data
    groups_collection = db['groups']  # Collection for group stats (for /stats)
    print("🝮︎︎︎ Connected to MongoDB 🝮︎︎︎")
except errors.ServerSelectionTimeoutError as err:
    print(f"Error: Could not connect to MongoDB: {err}")
    exit()

# List of sudo users (user IDs)
SUDO_USERS = [7222795580, 6180999156]  # Add user IDs of sudo users here

bot = telebot.TeleBot(API_TOKEN)

# Settings
BONUS_COINS = 50000  # Bonus amount for daily claim
BONUS_INTERVAL = timedelta(days=1)  # Bonus claim interval (24 hours)
COINS_PER_GUESS = 50  # Coins for correct guesses
STREAK_BONUS_COINS = 1000  # Additional coins for continuing a streak
FAST_GUESS_BONUS = 500  # Bonus coins for fast guesses
FAST_GUESS_THRESHOLD = 10  # Time in seconds for fast guesses
CHALLENGE_REWARD = 1000  # Reward for both challenger and friend if friend guesses correctly
DAILY_TOP_REWARD = 2000  # Daily reward for top fastest guessers
TOP_REWARD_COUNT = 3  # Number of top players to reward daily
# Updated rarity levels with new emoji
RARITY_LEVELS = {
    'Common': '🌟',    # Common
    'Rare': '🏮',      # Rare
    'Epic': '💥',      # Epic
    'Legendary': '🦠'  # Legendary
}
RARITY_WEIGHTS = [60, 25, 10, 5]
MESSAGE_THRESHOLD = 5  # Number of messages before sending a new character
GUESS_TIMEOUT = 60  # Timeout for sending a new character if no correct guess (in seconds)

# Global variables to track the current character and message count
current_character = None
global_message_count = 0  # Global counter for messages in all chats
guess_timer = None  # Timer for the guess timeout
character_post_time = None  # Track the time when the character was posted
current_challenger = None  # Track the user who initiated a challenge

# Helper Functions
def get_user_data(user_id):
    user = users_collection.find_one({'user_id': user_id})
    if user is None:
        new_user = {
            'user_id': user_id,
            'coins': 0,
            'correct_guesses': 0,
            'streak': 0,
            'total_guess_time': 0,
            'guess_count': 0,  # For tracking average guess time
            'last_bonus': None,
            'profile': None,
            'notifications': {'daily_rewards': False, 'leaderboard_updates': False}  # Notification settings
        }
        users_collection.insert_one(new_user)
        return new_user
    return user

def update_user_data(user_id, update_data):
    users_collection.update_one({'user_id': user_id}, {'$set': update_data})

# /profile Command to show user stats
@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    coins = user['coins']
    streak = user['streak']
    correct_guesses = user['correct_guesses']
    guess_count = user['guess_count']
    avg_guess_time = user['total_guess_time'] / guess_count if guess_count > 0 else 0

    profile_message = f"""
<b>🝮︎︎︎ Your Profile 🝮︎︎︎</b>

💰 <b>Coins:</b> {coins}
🔥 <b>Streak:</b> {streak} days
🎯 <b>Correct Guesses:</b> {correct_guesses}
⏱️ <b>Average Guess Time:</b> {avg_guess_time:.2f} seconds

🔔 <i>Notifications:</i>
Daily Rewards: {'✅' if user['notifications']['daily_rewards'] else '❌'}
Leaderboard Updates: {'✅' if user['notifications']['leaderboard_updates'] else '❌'}
"""
    bot.reply_to(message, profile_message, parse_mode='HTML')

# /subscribe and /unsubscribe Commands for notifications
@bot.message_handler(commands=['subscribe'])
def subscribe_notifications(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if 'daily_rewards' not in user['notifications']:
        user['notifications']['daily_rewards'] = False
        user['notifications']['leaderboard_updates'] = False
    
    update_user_data(user_id, {'notifications.daily_rewards': True, 'notifications.leaderboard_updates': True})

    bot.reply_to(message, "✅ You have successfully subscribed to notifications for daily rewards and leaderboard updates.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_notifications(message):
    user_id = message.from_user.id
    update_user_data(user_id, {'notifications.daily_rewards': False, 'notifications.leaderboard_updates': False})

    bot.reply_to(message, "❌ You have successfully unsubscribed from notifications.")

# Welcome message with personalized stats
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user['profile']:
        profile_name = message.from_user.full_name
        update_user_data(user_id, {'profile': profile_name})

    # Get personalized stats
    coins = user['coins']
    streak = user['streak']
    correct_guesses = user['correct_guesses']

    welcome_message = f"""
<b>🝮︎︎︎ Welcome to Pʜɪʟᴏ Gʀᴀʙʙᴇʀ 🝮︎︎︎</b>

🎮 Ready to dive into the world of anime characters? Let’s start collecting and guessing!

🝮︎︎︎ Your Stats:
💰 <b>Coins:</b> {coins}
🔥 <b>Streak:</b> {streak} days
🎯 <b>Correct Guesses:</b> {correct_guesses}

🔔 <i>Tip:</i> You can configure notifications for daily rewards or challenges using /subscribe and /unsubscribe!
"""
    markup = InlineKeyboardMarkup()
    developer_button = InlineKeyboardButton(text="Developer - @TechPiro", url="https://t.me/TechPiro")
    markup.add(developer_button)

    bot.send_message(message.chat.id, welcome_message, parse_mode='HTML', reply_markup=markup)

# /help Command to display all commands
@bot.message_handler(commands=['help'])
def show_help(message):
    help_message = """
<b>📜 🝮︎︎︎ Available Commands 🝮︎︎︎ 📜</b>

🎮 <b>Character Commands:</b>
/bonus - Claim your daily bonus 🝮︎︎︎
/challenge - Challenge a friend by replying to their message 🝮︎︎︎
/profile - View your personal stats 🝮︎︎︎
/fastest - View the top 10 fastest guessers 🝮︎︎︎
/topcoins - Show the top 10 users by coins 🝮︎︎︎

🏆 <b>Leaderboards and Stats:</b>
/stats - Show the bot's stats (Owner only) 🝮︎︎︎
/fastest - Show the leaderboard for fastest guessers 🝮︎︎︎

🔔 <b>Notifications:</b>
/subscribe - Subscribe to notifications for daily rewards and leaderboard updates 🝮︎︎︎
/unsubscribe - Unsubscribe from notifications 🝮︎︎︎

🛠️ <b>Admin Commands:</b>
/upload - Upload a new character (Sudo only) 🝮︎︎︎
/delete - Delete a character by ID (Sudo only) 🝮︎︎︎

ℹ️ <b>Other:</b>
/help - Show this help message 🝮︎︎︎

🝮︎︎︎ Daily Rewards: Top 3 fastest guessers receive bonus coins every day! Keep guessing fast! ⚡
🝮︎︎︎ Fast Guess Bonus: Guess in under 10 seconds to get an extra 500 coins! ⚡

🝮︎︎︎ Have fun and start collecting! 🝮︎︎︎
"""
    bot.reply_to(message, help_message, parse_mode='HTML')

# Handle all types of messages and increment the message counter
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global current_character, global_message_count, character_post_time, current_challenger
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_guess = message.text.strip().lower() if message.text else ""

    if message.chat.type in ['group', 'supergroup']:
        global_message_count += 1

    if global_message_count >= MESSAGE_THRESHOLD:
        send_character(chat_id)
        global_message_count = 0

    if current_character and user_guess:
        character_name = current_character['character_name'].strip().lower()

        if user_guess in character_name:
            user = get_user_data(user_id)
            new_coins = user['coins'] + COINS_PER_GUESS
            user['correct_guesses'] += 1
            user['streak'] += 1
            streak_bonus = STREAK_BONUS_COINS * user['streak']

            # Calculate time taken to guess
            guess_time = (datetime.now() - character_post_time).total_seconds()
            user['total_guess_time'] += guess_time
            user['guess_count'] += 1

            update_data = {
                'coins': new_coins + streak_bonus,
                'correct_guesses': user['correct_guesses'],
                'streak': user['streak'],
                'total_guess_time': user['total_guess_time'],
                'guess_count': user['guess_count']
            }

            # If user guessed in less than the FAST_GUESS_THRESHOLD, give a bonus
            if guess_time <= FAST_GUESS_THRESHOLD:
                new_coins += FAST_GUESS_BONUS
                update_data['coins'] = new_coins
                bot.reply_to(message, f"⚡ Fast Guess! You guessed correctly in {guess_time:.2f} seconds and earned an extra {FAST_GUESS_BONUS} coins! 🝮︎︎︎")

            # If the user was challenged by a friend, reward both the challenger and the friend
            if current_challenger and current_challenger != user_id:
                challenger = get_user_data(current_challenger)
                challenger['coins'] += CHALLENGE_REWARD
                user['coins'] += CHALLENGE_REWARD
                update_user_data(current_challenger, {'coins': challenger['coins']})
                bot.send_message(current_challenger, f"🎉 Your friend guessed correctly! You both receive {CHALLENGE_REWARD} coins! 🝮︎︎︎")
                bot.reply_to(message, f"🎉 You guessed correctly and both you and your friend receive {CHALLENGE_REWARD} coins! 🝮︎︎︎")
                current_challenger = None  # Reset the challenger after the challenge is completed

            update_user_data(user_id, update_data)

            avg_guess_time = get_average_guess_time(user)

            bot.reply_to(message, f"🎉 Congratulations! You guessed correctly and earned {COINS_PER_GUESS} coins! 🝮︎︎︎\n"
                                  f"🔥 Streak Bonus: {streak_bonus} coins for a {user['streak']}-guess streak! 🝮︎︎︎\n"
                                  f"⏱️ Average Guess Time: {avg_guess_time:.2f} seconds")

            send_new_character(chat_id)  # Send the next character

# Background task to run the scheduled events
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Start polling the bot
bot.infinity_polling(timeout=60, long_polling_timeout=60)
l
