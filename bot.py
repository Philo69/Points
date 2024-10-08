import telebot
from pymongo import MongoClient
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Replace with your actual bot API token and Telegram channel ID
API_TOKEN = "7825167784:AAERTUGH7iF67zhaMCSynHktBXS0sbqvWMA"
BOT_OWNER_ID = 7222795580  # Replace with the owner’s Telegram ID
CHANNEL_ID = -1002438449944  # Replace with your Telegram channel ID where characters are logged

# MongoDB Connection
MONGO_URI = "mongodb+srv://PhiloWise:Philo@waifu.yl9tohm.mongodb.net/?retryWrites=true&w=majority&appName=Waifu"
client = MongoClient(MONGO_URI)
db = client['philo_grabber']  # Database name
users_collection = db['users']  # Collection for user data
characters_collection = db['characters']  # Collection for character data
groups_collection = db['groups']  # Collection for group stats (for /stats)

# List of sudo users (user IDs)
SUDO_USERS = [7222795580, 6180999156]  # Add user IDs of sudo users here

bot = telebot.TeleBot(API_TOKEN)

# Settings
BONUS_COINS = 50000  # Bonus amount for daily claim
BONUS_INTERVAL = timedelta(days=1)  # Bonus claim interval (24 hours)
COINS_PER_GUESS = 50  # Coins for correct guesses
STREAK_BONUS_COINS = 1000  # Additional coins for continuing a streak
RARITY_LEVELS = {
    'Common': '⭐',
    'Rare': '🌟',
    'Epic': '💫',
    'Legendary': '✨'
}
RARITY_WEIGHTS = [60, 25, 10, 5]
MESSAGE_THRESHOLD = 5  # Number of messages before sending a new character
TOP_LEADERBOARD_LIMIT = 10  # Limit for leaderboard to only show top 10 users
ITEMS_PER_PAGE = 5  # Number of characters per page in inventory

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
            'profile': None
        }
        users_collection.insert_one(new_user)
        return new_user
    return user

def update_user_data(user_id, update_data):
    users_collection.update_one({'user_id': user_id}, {'$set': update_data})

def get_user_rank(user_id):
    user = get_user_data(user_id)
    user_coins = user['coins']

    # Count users with more coins than the current user
    higher_ranked_users = users_collection.count_documents({'coins': {'$gt': user_coins}})
    # Total users
    total_users = users_collection.count_documents({})

    # Rank is one more than the number of users with more coins (as rank 1 is the top player)
    rank = higher_ranked_users + 1

    # Find the user directly above the current user in rank (for "next rank" calculation)
    next_user = users_collection.find_one({'coins': {'$gt': user_coins}}, sort=[('coins', 1)])
    if next_user:
        coins_to_next_rank = next_user['coins'] - user_coins
    else:
        coins_to_next_rank = None  # User is already at the highest rank

    return rank, total_users, coins_to_next_rank

def get_character_data():
    return list(characters_collection.find())

def add_character(image_url, character_name, rarity):
    character_id = characters_collection.count_documents({}) + 1
    character = {
        'id': character_id,
        'image_url': image_url,
        'character_name': character_name,
        'rarity': rarity
    }
    characters_collection.insert_one(character)
    return character

def assign_rarity():
    return random.choices(list(RARITY_LEVELS.keys()), weights=RARITY_WEIGHTS, k=1)[0]

def fetch_new_character():
    characters = get_character_data()
    if characters:
        return random.choice(characters)
    return None

def send_character(chat_id):
    global current_character
    current_character = fetch_new_character()
    if current_character:
        rarity = RARITY_LEVELS[current_character['rarity']]
        caption = (
            f"🎨 Guess the Anime Character!\n\n"
            f"💬 Name: ???\n"
            f"⚔️ Rarity: {rarity} {current_character['rarity']}\n"
        )
        bot.send_photo(chat_id, current_character['image_url'], caption=caption)

def is_owner_or_sudo(user_id):
    return user_id == BOT_OWNER_ID or user_id in SUDO_USERS

# Command Handlers

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if not user['profile']:
        profile_name = message.from_user.full_name
        update_user_data(user_id, {'profile': profile_name})

    welcome_message = """
<b>🝮︎︎︎︎︎︎︎ Welcome to Pʜɪʟᴏ 🝮︎︎︎︎︎︎︎ Gʀᴀʙʙᴇʀ 🝮︎︎︎︎︎︎︎</b>

🎮 Ready to dive into the world of anime characters? Let’s start collecting and guessing!

🝮︎︎︎︎︎︎︎ Use the commands below to explore all the features!
"""
    # Creating an inline button for developer link
    markup = InlineKeyboardMarkup()
    developer_button = InlineKeyboardButton(text="Developer - @TechPiro", url="https://t.me/TechPiro")
    markup.add(developer_button)

    bot.send_message(message.chat.id, welcome_message, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_message = """
<b>📜 🝮︎︎︎︎︎︎︎ Available Commands 🝮︎︎︎︎︎︎︎ 📜</b>

🎮 <b>Character Commands:</b>
/bonus - Claim your daily bonus 🝮︎︎︎︎︎︎︎
/inventory - View your character inventory 🝮︎︎︎︎︎︎︎
/gift - Gift coins to another user by tagging them 🝮︎︎︎︎︎︎︎
/profile - Show your personal stats (rank, coins, guesses, etc.) 🝮︎︎︎︎︎︎︎

🏆 <b>Leaderboards:</b>
/leaderboard - Show the top 10 users by coins 🝮︎︎︎︎︎︎︎
/topcoins - Show the top 10 users by coins earned today 🝮︎︎︎︎︎︎︎

📊 <b>Bot Stats:</b>
/stats - Show the bot's stats (total users, characters, groups) 🝮︎︎︎︎︎︎︎

ℹ️ <b>Miscellaneous:</b>
/help - Show this help message 🝮︎︎︎︎︎︎︎

🝮︎︎︎︎︎︎︎ Have fun and start collecting! 🝮︎︎︎︎︎︎︎
"""
    bot.reply_to(message, help_message, parse_mode='HTML')

# /stats command to show bot stats
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != BOT_OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to view this information.")
        return

    total_users = users_collection.count_documents({})
    total_characters = characters_collection.count_documents({})
    total_groups = groups_collection.count_documents({})

    stats_message = f"""
<b>📊 🝮︎︎︎︎︎︎︎ Bot Stats 🝮︎︎︎︎︎︎︎:</b>
- 🧑‍🤝‍🧑 Total Users: {total_users}
- 🎎 Total Characters: {total_characters}
- 👥 Total Groups: {total_groups}
"""
    bot.reply_to(message, stats_message, parse_mode='HTML')

# /gift command to send coins to another user by tagging them
@bot.message_handler(commands=['gift'])
def gift_coins(message):
    sender_id = message.from_user.id
    sender = get_user_data(sender_id)

    # Validate the command format
    if len(message.text.split()) < 2 or not message.reply_to_message:
        bot.reply_to(message, "❌ Invalid format. Use `/gift <amount>` and tag a user.")
        return

    try:
        amount = int(message.text.split()[1])
    except ValueError:
        bot.reply_to(message, "❌ The amount must be a number.")
        return

    # Ensure the sender has enough coins
    if sender['coins'] < amount:
        bot.reply_to(message, "❌ You don't have enough coins to gift.")
        return

    # Ensure a user is tagged (recipient)
    if not message.reply_to_message.from_user:
        bot.reply_to(message, "❌ You need to tag a user to send coins.")
        return

    recipient_id = message.reply_to_message.from_user.id
    recipient = get_user_data(recipient_id)

    # Transfer coins
    sender_new_coins = sender['coins'] - amount
    recipient_new_coins = recipient['coins'] + amount
    update_user_data(sender_id, {'coins': sender_new_coins})
    update_user_data(recipient_id, {'coins': recipient_new_coins})

    # Send confirmation messages
    bot.reply_to(message, f"🎁 You have successfully gifted {amount} coins to {message.reply_to_message.from_user.first_name}!")
    bot.send_message(recipient_id, f"🎉 You have received {amount} coins from {message.from_user.first_name}!")

# Start polling the bot
bot.infinity_polling(timeout=60, long_polling_timeout=60)
