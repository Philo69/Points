import random
import string
import requests
import re
import aiosqlite
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Define the bot owner's user ID
BOT_OWNER_ID = 7202072688  # Replace with your actual Telegram user ID
BOT_TOKEN = "7779270006:AAFgPtHaKTaz9SuSkE6WmbUHG_IpKhPMIag"  # Replace this with your actual bot token

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
    await update.message.reply_text(
        "🎉 Welcome to Good Charged Bot! 🎉\n\n"
        "Use /help to explore all the available commands."
    )

# /help command showing all commands
async def help_command(update: Update, context: CallbackContext) -> None:
    help_message = (
        "<b>Available Commands:</b>\n\n"
        "• /start - Show a welcome message\n"
        "• /help - Show this help message\n"
        "• /redeem <key> - Redeem a key to become premium and receive credits\n"
        "• /generatekey <user_id> <credits> <number_of_codes> - (Owner Only) Generate multiple redemption keys\n"
        "• /gateway <url> - Check if a website uses 2D or 3D Stripe payments\n"
    )
    await update.message.reply_text(help_message, parse_mode="HTML")

# /generatekey command (Owner Only) to create multiple keys for a specific plan
async def generatekey_command(update: Update, context: CallbackContext) -> None:
    # Ensure only the bot owner can generate codes
    user_id = update.message.from_user.id
    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("You are not authorized to generate keys.")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /generatekey <user_id> <credits_per_code> <number_of_codes>")
        return
    
    try:
        target_user_id = int(context.args[0])
        credits_per_code = int(context.args[1])
        num_codes = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Invalid input. Please provide valid user ID, credits, and number of codes.")
        return

    codes = []
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            for _ in range(num_codes):
                key = generate_random_key()  # Generate a unique random key
                codes.append(key)
                await cursor.execute("INSERT INTO redemption_keys (key, user_id, credits) VALUES (?, ?, ?)", 
                                     (key, target_user_id, credits_per_code))
            await conn.commit()

    # Format the response message
    code_list = "\n".join([f"⦋ϟ⦌ {code}" for code in codes])
    message = (
        "✅ Plan codes Generated!\n\n"
        "- Charged Redeem Codes -\n"
        "━━━━━━━━━━━\n"
        f"Plan: Premium | ⌚ 2d | 🔢 {num_codes}\n"
        "━━━━━━━━━━━\n\n"
        f"{code_list}\n\n"
        "━━━━━━━━━━━\n"
        f"Each code contains {credits_per_code} credits.\n"
        "⦋ϟ⦌ Authorised By [t.me/AlwaysToShine](https://t.me/AlwaysToShine)"
    )

    # Send the formatted message to the bot owner
    await update.message.reply_text(message)

# Function to redeem a key
async def redeem_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    if len(context.args) == 0:
        await update.message.reply_text("Please provide a redemption key. Example: /redeem ABCD1234")
        return
    
    key = context.args[0]

    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT user_id, credits, redeemed FROM redemption_keys WHERE key=?", (key,))
            result = await cursor.fetchone()

            if result is None:
                await update.message.reply_text("Invalid redemption key.")
                return

            target_user_id, credits, redeemed = result

            if redeemed == 1:
                await update.message.reply_text("This key has already been redeemed.")
                return

            if target_user_id != user_id:
                await update.message.reply_text("This key is not assigned to your account.")
                return

            await cursor.execute("UPDATE redemption_keys SET redeemed = 1 WHERE key=?", (key,))
            await cursor.execute("SELECT credits FROM user_points WHERE user_id=?", (user_id,))
            user_result = await cursor.fetchone()

            if user_result is None:
                await cursor.execute("INSERT INTO user_points (user_id, username, credits, premium) VALUES (?, ?, ?, ?)", 
                                     (user_id, username, credits, 1))
            else:
                current_credits = user_result[0]
                await cursor.execute("UPDATE user_points SET credits = ?, premium = ? WHERE user_id = ?", 
                                     (current_credits + credits, 1, user_id))
            await conn.commit()

    await update.message.reply_text(
        f"🎊 Key redeemed successfully! 🎊\n\n"
        f"You are now a premium User with {credits} credits! 💎"
    )

# /gateway command to check if a site uses 2D or 3D Stripe
async def gateway_command(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a website URL. Example: /gateway https://example.com")
        return

    url = context.args[0]

    if not url.startswith("http"):
        url = "http://" + url

    try:
        # Fetch the website content
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Analyze the website content
        site_content = response.text

        stripe_info = {
            "checkout": "Not available",
            "type": "Unknown",
            "cs_live": "Not available",
            "pk_live": "Not available",
            "client_secret": "Not available"
        }

        # Check for Stripe references
        if 'stripe.js' in site_content.lower() or 'checkout.stripe.com' in site_content.lower():
            stripe_info['checkout'] = "HERE"
        
        # Detect 2D or 3D type by looking for 3D secure-related terms
        if '3dsecure' in site_content.lower() or '3ds' in site_content.lower():
            stripe_info['type'] = "3D Stripe"
        elif 'stripe.js' in site_content.lower() or 'checkout.stripe.com' in site_content.lower():
            stripe_info['type'] = "2D Stripe"

        # Extract PK_live and CS_live keys using regular expressions
        pk_live_match = re.search(r'pk_live_[A-Za-z0-9]+', site_content)
        cs_live_match = re.search(r'cs_live_[A-Za-z0-9]+', site_content)

        if pk_live_match:
            stripe_info['pk_live'] = pk_live_match.group(0)
        if cs_live_match:
            stripe_info['cs_live'] = cs_live_match.group(0)

        # Extract Client Secret
        client_secret_match = re.search(r'client_secret_[A-Za-z0-9]+', site_content)
        if client_secret_match:
            stripe_info['client_secret'] = client_secret_match.group(0)

        # Format and send the Stripe Checkout info
        message = (
            "Stripe Checkout info: ✅\n\n"
            f"🔗 Checkout: {stripe_info['checkout']}\n"
            f"⦋ϟ⦌ Type: {stripe_info['type']}\n\n"
            f"⦋ϟ⦌ CS_live: {stripe_info['cs_live']}\n"
            f"⦋ϟ⦌ PK_live: {stripe_info['pk_live']}\n"
            f"⦋ϟ⦌ Client Secret: {stripe_info['client_secret']}\n\n"
            "⦋ϟ⦌ Authorised By [t.me/AlwaysToShine](https://t.me/AlwaysToShine)"
        )

        await update.message.reply_text(message)

    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Error accessing {url}: {str(e)}")

# Initialize the bot application and run it
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("redeem", redeem_command))  # Redeem command for users
    application.add_handler(CommandHandler("generatekey", generatekey_command))  # Owner command to generate keys
    application.add_handler(CommandHandler("gateway", gateway_command))  # Check Stripe gateway

    # Start the bot
    await application.start()
    await application.process_updates()

    # Idle to keep the bot running
    await application.idle()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
