import telebot
import random
from pymongo import MongoClient
from datetime import datetime, timedelta
from threading import Timer

# Replace with your actual bot API token and Telegram channel ID
API_TOKEN = "7825167784:AAH4I6FpeF4ATOZotfwCZBsgmdoeKtpvKBo"
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

# /start command to welcome users and show the help message
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_message = """
<b>🝮︎︎︎︎︎︎︎ Welcome to Pʜɪʟᴏ 🝮︎︎︎︎︎︎︎ Gʀᴀʙʙᴇʀ 🝮︎︎︎︎︎︎︎</b>

🎮 Ready to dive into the world of anime characters? Let’s start collecting and guessing!

Incline developer: <a href="https://t.me/TechPiro">@TechPiro</a>

🝮︎︎︎︎︎︎︎ Use the commands below to explore all the features!
"""
    bot.send_message(message.chat.id, welcome_message, parse_mode='HTML')
    show_help(message)

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

# Fix /leaderboard command to show top users by coins
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    top_users = users_collection.find().sort("coins", -1).limit(10)
    leaderboard_message = "<b>🏆 🝮︎︎︎︎︎︎︎ Top 10 Users by Coins 🝮︎︎︎︎︎︎︎ 🏆</b>\n\n"

    for index, user in enumerate(top_users, start=1):
        profile_name = user.get('profile', 'Unknown User')
        telegram_username = user.get('username', None)

        if telegram_username:
            profile_mention = f"[{profile_name}](tg://user?id={user['user_id']})"
        else:
            profile_mention = profile_name

        leaderboard_message += f"{index}. {profile_mention} — {user['coins']} coins 🝮︎︎︎︎︎︎︎\n"

    bot.reply_to(message, leaderboard_message, parse_mode='Markdown')

# Fix /topcoins command to show users with the most coins earned today
@bot.message_handler(commands=['topcoins'])
def topcoins(message):
    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    top_users_today = users_collection.find({"last_bonus": {"$gte": start_of_day.strftime('%Y-%m-%d %H:%M:%S')}}).sort("coins", -1).limit(10)

    topcoins_message = "<b>🌟 🝮︎︎︎︎︎︎︎ Top 10 Users by Coins Earned Today 🝮︎︎︎︎︎︎︎ 🌟</b>\n\n"

    for index, user in enumerate(top_users_today, start=1):
        profile_name = user.get('profile', 'Unknown User')
        telegram_username = user.get('username', None)

        if telegram_username:
            profile_mention = f"[{profile_name}](tg://user?id={user['user_id']})"
        else:
            profile_mention = profile_name

        topcoins_message += f"{index}. {profile_mention} — {user['coins']} coins 🝮︎︎︎︎︎︎︎\n"

    bot.reply_to(message, topcoins_message, parse_mode='Markdown')

# /help command to show available commands
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = """
<b>📜 🝮︎︎︎︎︎︎︎ Available Commands 🝮︎︎︎︎︎︎︎ 📜</b>

/help - Show this help message
/inventory - View your character inventory
/leaderboard - Show the top 10 users by coins 🝮︎︎︎︎︎︎︎
/bonus - Claim your daily bonus 🝮︎︎︎︎︎︎︎
/gift - Gift coins to another user by tagging them
/topcoins - Show the top 10 users by coins earned today 🝮︎︎︎︎︎︎︎
/profile - Show your personal stats (rank, coins, guesses, etc.)
/stats - Show the bot's stats (total users, characters, groups)
"""
    bot.reply_to(message, help_text, parse_mode='HTML')

# /profile command to show user's rank, total users, and personal stats
@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)

    if not user:
        bot.reply_to(message, "❌ User not found.")
        return

    streak = user.get('streak', 0)
    coins = user.get('coins', 0)
    correct_guesses = user.get('correct_guesses', 0)

    total_users = users_collection.count_documents({})

    # Rank the user based on their coins
    rank = users_collection.count_documents({"coins": {"$gt": coins}}) + 1

    profile_message = f"""
<b>📊 🝮︎︎︎︎︎︎︎ Your Profile 🝮︎︎︎︎︎︎︎:</b>
- 💰 Coins: {coins}
- 🔥 Streak: {streak}
- 🎯 Correct Guesses: {correct_guesses}
- 🏅 Rank: {rank} / {total_users} users 🝮︎︎︎︎︎︎︎
"""
    bot.reply_to(message, profile_message, parse_mode='HTML')

# /stats command to show bot's stats (total users, characters, groups, etc.)
@bot.message_handler(commands=['stats'])
def show_stats(message):
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

# Handle all types of messages and increment the message counter
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    global global_message_count
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.chat.type in ['group', 'supergroup']:
        group_data = get_group_data(chat_id)
        new_message_count = group_data['message_count'] + 1
        update_group_data(chat_id, {'message_count': new_message_count})

    user_guess = message.text.strip().lower() if message.text else ""

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
            update_user_data(user_id, {
                'coins': new_coins + streak_bonus,
                'correct_guesses': user['correct_guesses'],
                'streak': user['streak'],
                'inventory': user['inventory'] + [current_character]
            })
            bot.reply_to(message, f"🎉 Congratulations! You guessed correctly and earned {COINS_PER_GUESS} coins! 🝮︎︎︎︎︎︎︎\n"
                                  f"🔥 Streak Bonus: {streak_bonus} coins for a {user['streak']}-guess streak! 🝮︎︎︎︎︎︎︎")
            send_character(chat_id)
        else:
            update_user_data(user_id, {'streak': 0})

# Start polling the bot
print("🝮︎︎︎︎︎︎︎ Bot is running... 🝮︎︎︎︎︎︎︎")
bot.infinity_polling(timeout=10, long_polling_timeout=5)
