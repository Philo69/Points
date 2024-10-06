import telebot
import random
from pymongo import MongoClient
from datetime import datetime, timedelta
from threading import Timer
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Replace with your actual bot API token and Telegram channel ID
API_TOKEN = "7825167784:AAGSuh-tlImyH3_Zwp5Ehb0LiBDXLlLBGjg"
BOT_OWNER_ID = 7222795580  # Replace with the owner’s Telegram ID
CHANNEL_ID = -1002438449944  # Replace with your Telegram channel ID where characters are logged

# MongoDB Connection
MONGO_URI = "mongodb+srv://PhiloWise:Philo@waifu.yl9tohm.mongodb.net/?retryWrites=true&w=majority&appName=Waifu"
try:
    client = MongoClient(MONGO_URI)
    db = client['philo_grabber']  # Database name
    users_collection = db['users']  # Collection for user data
    characters_collection = db['characters']  # Collection for character data
    groups_collection = db['groups']  # Collection for group stats
    print("🝮︎︎︎︎︎︎︎ Connected to MongoDB 🝮︎︎︎︎︎︎︎")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    exit()  # Exit if connection fails

# Initialize the bot
bot = telebot.TeleBot(API_TOKEN)

# Settings
BONUS_COINS = 50000  # Bonus amount for daily claim
BONUS_INTERVAL = timedelta(days=1)  # Bonus claim interval (24 hours)
COINS_PER_GUESS = 50  # Coins for correct guesses
STREAK_BONUS_COINS = 1000  # Additional coins for continuing a streak
MESSAGE_THRESHOLD = 5  # Number of messages before sending a new character
current_character = None
global_message_count = 0  # Global counter for messages in all chats
REMINDER_INTERVAL = 24 * 60 * 60  # 24 hours for reminder

# Define valid rarities with your unique emojis
RARITY_EMOJIS = {
    'Common': '🌟',       # Emoji for Common
    'Rare': '🏮',         # Emoji for Rare
    'Epic': '🧿',         # Emoji for Epic
    'Legendary': '🔮'     # Emoji for Legendary
}
VALID_RARITIES = list(RARITY_EMOJIS.keys())  # ['Common', 'Rare', 'Epic', 'Legendary']

# Define sudo (admin) users (including bot owner)
sudo_users = [6180999156, 7222795580]  # Added your admin user IDs

# Helper Functions
def get_user_data(user_id):
    user = users_collection.find_one({'user_id': user_id})
    if user is None:
        new_user = {
            'user_id': user_id,
            'coins': 0,
            'correct_guesses': 0,
            'inventory': [],
            'last_bonus': None,
            'streak': 0,
            'profile': None,
            'username': None
        }
        users_collection.insert_one(new_user)
        return new_user
    return user

def update_user_data(user_id, update_data):
    users_collection.update_one({'user_id': user_id}, {'$set': update_data})

def get_group_data(group_id):
    group = groups_collection.find_one({'group_id': group_id})
    if group is None:
        new_group = {
            'group_id': group_id,
            'group_name': None,
            'message_count': 0
        }
        groups_collection.insert_one(new_group)
        return new_group
    return group

def update_group_data(group_id, update_data):
    groups_collection.update_one({'group_id': group_id}, {'$set': update_data})

# /upload command to add new characters to the database with rarity validation and emojis
@bot.message_handler(commands=['upload'])
def upload_character(message):
    user_id = message.from_user.id

    # Check if the user is the owner or a sudo user
    if user_id != BOT_OWNER_ID and user_id not in sudo_users:
        bot.reply_to(message, "❌ You do not have permission to upload characters.")
        return

    try:
        # Expecting the format: /upload <character_name> <image_url> <rarity>
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            bot.reply_to(message, "❌ Incorrect format. Use /upload <character_name> <image_url> <rarity>")
            return

        character_name = parts[1]
        image_url = parts[2]
        rarity = parts[3].capitalize()  # Capitalize rarity input to ensure case-insensitivity

        # Check if rarity is valid
        if rarity not in VALID_RARITIES:
            bot.reply_to(message, f"❌ Invalid rarity. Please choose from: {', '.join(VALID_RARITIES)}")
            return

        # Check if character already exists
        existing_character = characters_collection.find_one({'character_name': character_name})
        if existing_character:
            bot.reply_to(message, "❌ A character with this name already exists in the database.")
            return

        # Insert the new character into the database
        new_character = {
            'character_name': character_name,
            'image_url': image_url,
            'rarity': rarity
        }
        characters_collection.insert_one(new_character)
        emoji = RARITY_EMOJIS[rarity]
        bot.reply_to(message, f"✅ Successfully uploaded character: {character_name} {emoji} (Rarity: {rarity}) 🝮︎︎︎︎︎︎︎")

    except Exception as e:
        bot.reply_to(message, f"❌ Error occurred: {str(e)}")

# /delete command to remove characters from the database, only for sudo users
@bot.message_handler(commands=['delete'])
def delete_character(message):
    user_id = message.from_user.id
    if user_id != BOT_OWNER_ID and user_id not in sudo_users:
        bot.reply_to(message, "❌ You do not have permission to delete characters.")
        return

    try:
        # Expecting the format: /delete <character_name>
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "❌ Incorrect format. Use /delete <character_name>")
            return

        character_name = parts[1]

        # Check if character exists
        character = characters_collection.find_one({'character_name': character_name})
        if not character:
            bot.reply_to(message, "❌ No character with this name exists.")
            return

        # Delete the character from the database
        characters_collection.delete_one({'character_name': character_name})
        bot.reply_to(message, f"✅ Successfully deleted character: {character_name} 🝮︎︎︎︎︎︎︎")

    except Exception as e:
        bot.reply_to(message, f"❌ Error occurred: {str(e)}")

# /bonus command to claim daily bonus and send reminder for next claim
@bot.message_handler(commands=['bonus'])
def claim_bonus(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    last_bonus_time = user.get('last_bonus')
    now = datetime.now()

    if last_bonus_time is not None:
        last_bonus_time = datetime.strptime(last_bonus_time, '%Y-%m-%d %H:%M:%S')
        if now - last_bonus_time < BONUS_INTERVAL:
            remaining_time = BONUS_INTERVAL - (now - last_bonus_time)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            bot.reply_to(message, f"⏳ You can claim your next bonus in {hours} hours, {minutes} minutes.")
            return

    # Grant the bonus
    user['coins'] += BONUS_COINS
    user['last_bonus'] = now.strftime('%Y-%m-%d %H:%M:%S')
    update_user_data(user_id, user)

    # Reminder for the next bonus claim after 24 hours
    Timer(REMINDER_INTERVAL, lambda: bot.send_message(user_id, "🝮︎︎︎︎︎︎︎ 💡 Time to claim your bonus again!")).start()
    
    bot.reply_to(message, f"🎁 You've claimed your daily bonus of {BONUS_COINS} coins! 🝮︎︎︎︎︎︎︎")

# /gift command to gift coins to another user by tagging them
@bot.message_handler(commands=['gift'])
def gift_coins(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❌ You need to reply to a user to gift coins.")
        return

    try:
        parts = message.text.split()
        amount = int(parts[1])
        if amount <= 0:
            bot.reply_to(message, "❌ The amount of coins must be greater than 0.")
            return
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Incorrect format. Use /gift <amount> while replying to a user.")
        return

    sender_id = message.from_user.id
    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        bot.reply_to(message, "❌ You cannot gift coins to yourself.")
        return

    sender = get_user_data(sender_id)
    receiver = get_user_data(receiver_id)

    if sender['coins'] < amount:
        bot.reply_to(message, "❌ You do not have enough coins to gift.")
        return

    # Transfer coins
    sender['coins'] -= amount
    receiver['coins'] += amount

    update_user_data(sender_id, sender)
    update_user_data(receiver_id, receiver)

    bot.reply_to(message, f"✅ You successfully gifted {amount} coins to {message.reply_to_message.from_user.first_name}! 🝮︎︎︎︎︎︎︎")

# /leaderboard command to show top users by coins
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    top_users = users_collection.find().sort("coins", -1).limit(10)
    leaderboard_message = "<b>🏆 🝮︎︎︎︎︎︎︎ Top 10 Users by Coins 🝮︎︎︎︎︎︎︎ 🏆</b>\n\n"

    if top_users.count() == 0:
        bot.reply_to(message, "❌ No users found on the leaderboard.")
        return

    for index, user in enumerate(top_users, start=1):
        profile_name = user.get('profile', 'Unknown User')
        telegram_username = user.get('username', None)

        if telegram_username:
            profile_mention = f"[{profile_name}](tg://user?id={user['user_id']})"
        else:
            profile_mention = profile_name

        leaderboard_message += f"{index}. {profile_mention} — {user['coins']} coins 🝮︎︎︎︎︎︎︎\n"

    bot.reply_to(message, leaderboard_message, parse_mode='Markdown')

# /topcoins command to show users with the most coins earned today
@bot.message_handler(commands=['topcoins'])
def topcoins(message):
    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    top_users_today = users_collection.find({"last_bonus": {"$gte": start_of_day.strftime('%Y-%m-%d %H:%M:%S')}}).sort("coins", -1).limit(10)

    topcoins_message = "<b>🌟 🝮︎︎︎︎︎︎︎ Top 10 Users by Coins Earned Today 🝮︎︎︎︎︎︎︎ 🌟</b>\n\n"

    if top_users_today.count() == 0:
        bot.reply_to(message, "❌ No users have earned coins today.")
        return

    for index, user in enumerate(top_users_today, start=1):
        profile_name = user.get('profile', 'Unknown User')
        telegram_username = user.get('username', None)

        if telegram_username:
            profile_mention = f"[{profile_name}](tg://user?id={user['user_id']})"
        else:
            profile_mention = profile_name

        topcoins_message += f"{index}. {profile_mention} — {user['coins']} coins 🝮︎︎︎︎︎︎︎\n"

    bot.reply_to(message, topcoins_message, parse_mode='Markdown')

# Start polling the bot
print("🝮︎︎︎︎︎︎︎ Bot is running... 🝮︎︎︎︎︎︎︎")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
