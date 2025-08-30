from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import json
import os

API_TOKEN = API_TOKEN = "7723019625:AAE3rsIFzMSzxaFSKyCJL8U5xrHA69wZjNU"
USERS_FILE = "users_data.json"
TASKS_FILE = "tasks.json"

# Load users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users_data = json.load(f)
else:
    users_data = {}

# Load tasks
if os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "r") as f:
        tasks_data = json.load(f)
else:
    tasks_data = []

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

# Ensure user exists
def get_user(user_id, name):
    if user_id not in users_data:
        users_data[user_id] = {
            "name": name,
            "tasks_completed": [],
            "balance": 0.0,
            "wallet": 0.0
        }
        save_users()
    return users_data[user_id]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    get_user(user_id, user_name)

    keyboard = [
        [InlineKeyboardButton("View Tasks", callback_data="view_tasks")],
        [InlineKeyboardButton("Premium Tasks", callback_data="premium_tasks")],
        [InlineKeyboardButton("Check Balance", callback_data="check_balance")],
        [InlineKeyboardButton("Deposit Money", callback_data="deposit")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {user_name}! Welcome to MicroTask Bot 💰\n"
        "Complete small tasks and earn money.",
        reply_markup=reply_markup
    )

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    user_name = query.from_user.full_name
    user = get_user(user_id, user_name)

    if query.data == "check_balance":
        await query.edit_message_text(
            f"💰 Your Balance: ${user['balance']:.2f}\n"
            f"Wallet: ${user['wallet']:.2f}"
        )
    elif query.data == "withdraw":
        await query.edit_message_text(
            f"To withdraw your earnings, contact the admin.\nYour Balance: ${user['balance']:.2f}"
        )
    elif query.data == "deposit":
        await query.edit_message_text("Please type the amount to deposit (e.g., 1.50):")
        context.user_data["deposit"] = True
    elif query.data == "view_tasks":
        available_tasks = [t for t in tasks_data if not t.get("premium", False) and t["id"] not in user["tasks_completed"]]
        if not available_tasks:
            await query.edit_message_text("No free tasks available! Come back later.")
            return
        text = "Available Free Tasks:\n\n" + "\n\n".join([f"{t['id']}. {t['description']} - Reward: ${t['reward']}" for t in available_tasks])
        await query.edit_message_text(text)
    elif query.data == "premium_tasks":
        available_tasks = [t for t in tasks_data if t.get("premium", False) and t["id"] not in user["tasks_completed"]]
        available_tasks = [t for t in available_tasks if user["wallet"] >= t["price"]]
        if not available_tasks:
            await query.edit_message_text("No available premium tasks! Come back later or deposit more money.")
            return
        text = "Available Premium Tasks:\n\n" + "\n\n".join([f"{t['id']}. {t['description']} - Price: ${t['price']} Reward: ${t['reward']}" for t in available_tasks])
        await query.edit_message_text(text)

# Deposit handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    user = get_user(user_id, user_name)

    if context.user_data.get("deposit"):
        try:
            amount = float(update.message.text)
            if amount <= 0:
                await update.message.reply_text("Please enter a positive number.")
                return
            user["wallet"] += amount
            save_users()
            await update.message.reply_text(f"✅ Deposited ${amount:.2f} to your wallet.")
        except:
            await update.message.reply_text("❌ Invalid number. Try again.")
        context.user_data["deposit"] = False

# Main
app = ApplicationBuilder().token(API_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("Bot is running...")
app.run_polling()

