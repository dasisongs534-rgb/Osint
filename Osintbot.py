import telebot
from telebot import apihelper
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    BotCommand, BotCommandScopeDefault, BotCommandScopeChat
)
import threading
import io
import requests
import json

# ================= CONFIGURATION =================
TOKEN = '8976652730:AAHlwFdP1wo7GsjKyBZdDzx7SgIrhxglsuA'
ADMIN_ID = 8595123051
OWNER_NAME = "@Aditya_dark0"
CHANNELS = ["@AdityaXosint", "@zarionxmain", "@TheliteSocity", "@godhosts", "@thelitegiveaway"]

# ================= NETWORK FIXES =================
apihelper.RETRY_ON_ERROR = True
apihelper.READ_TIMEOUT = 90
apihelper.CONNECTION_TIMEOUT = 90

bot = telebot.TeleBot(TOKEN)

# ================= DATABASES (In-Memory) =================
users_db = {}           
pending_referrals = {}  
promos_db = {}          

# ================= PRICING & API KEYS =================
PRICES = {
    'num_info': 1, 'num_adv': 2, 'aadhaar_info': 2, 'aadhaar_adv': 3,
    'veh_owner': 5, 'veh_info': 2, 'email_info': 2, 'ig_info': 1, 'truecaller': 2
}

API_KEYS = {
    'num_info': 'nx_Auth_729xP',
    'num_adv': 'nxAdv_992_mKq',
    'aadhaar_info': 'nx_Auth_729xP',     
    'aadhaar_adv': 'nxAdv_992_mKq',
    'veh_owner': 'vOwn_515_pTx',
    'veh_info': 'vInf_883_rBn',
    'email_info': 'nxAdv_992_mKq',
    'ig_info': 'ig_662_jSd',
    'truecaller': 'tc_224_kGf'
}

# ================= UTILITY FUNCTIONS =================
def is_joined(user_id):
    for ch in CHANNELS:
        try:
            stat = bot.get_chat_member(ch, user_id).status
            if stat not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            return False 
    return True

def delete_msg(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# ================= USER COMMANDS =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id and user_id not in users_db:
            pending_referrals[user_id] = referrer_id

    if user_id not in users_db:
        users_db[user_id] = {"credits": 0, "verified": False}
        
    if is_joined(user_id):
        users_db[user_id]["verified"] = True

    if users_db[user_id]["verified"]:
        menu_cmd(message)
        return

    markup = InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify_join"))
    
    bot.send_message(message.chat.id, "Welcome! Please join our 5 channels and click Verify to get 8 Bonus Credits:", reply_markup=markup)

@bot.message_handler(commands=['menu'])
def menu_cmd(message):
    user_id = message.from_user.id
    
    if user_id not in users_db:
        users_db[user_id] = {"credits": 0, "verified": False}
        
    if not users_db[user_id]["verified"]:
        if is_joined(user_id):
            users_db[user_id]["verified"] = True
        else:
            bot.send_message(message.chat.id, "❌ Please /start and Verify channels first!")
            return
        
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Number Info", callback_data="num_info"),
        InlineKeyboardButton("Number Info Advance", callback_data="num_adv"),
        InlineKeyboardButton("Aadhaar Info", callback_data="aadhaar_info"),
        InlineKeyboardButton("Aadhaar Info Advance", callback_data="aadhaar_adv"),
        InlineKeyboardButton("Vehicle to Owner", callback_data="veh_owner"),
        InlineKeyboardButton("Vehicle Info", callback_data="veh_info"),
        InlineKeyboardButton("Email Lookup", callback_data="email_info"),
        InlineKeyboardButton("Instagram Info", callback_data="ig_info"),
        InlineKeyboardButton("Truecaller Info", callback_data="truecaller")
    )
    markup.add(
        InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
        InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer_earn")
    )
    markup.add(
        InlineKeyboardButton("🛒 Buy Credit", callback_data="buy_credit"),
        InlineKeyboardButton("⚙️ Buy API", callback_data="buy_api")
    )
    
    bot.send_message(message.chat.id, "📋 *MAIN MENU*\nSelect a service:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['redeem'])
def redeem_cmd(message):
    try:
        code = message.text.split()[1]
        user_id = message.from_user.id
        if code in promos_db:
            promo = promos_db[code]
            if user_id in promo['used_by']:
                bot.reply_to(message, "❌ You have already redeemed this code!")
            elif len(promo['used_by']) >= promo['limit']:
                bot.reply_to(message, "❌ This promo code has reached its maximum limit or expired.")
            else:
                promo['used_by'].append(user_id)
                users_db[user_id]["credits"] += promo['amount']
                bot.reply_to(message, f"✅ Promo Redeemed! You received {promo['amount']} credits.")
        else:
            bot.reply_to(message, "❌ Invalid or Expired Promo Code.")
    except IndexError:
        bot.reply_to(message, "Usage: /redeem <promo_code>")

# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=['add'])
def add_balance(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        msg = bot.reply_to(message, "Enter amount to add:")
        bot.register_next_step_handler(msg, lambda m: process_add(m, target_id))
    except:
        bot.reply_to(message, "Usage: /add <user_id>")

def process_add(message, target_id):
    amount = int(message.text)
    if target_id not in users_db:
        users_db[target_id] = {"credits": 0, "verified": False}
    users_db[target_id]["credits"] += amount
    bot.reply_to(message, f"✅ Added {amount} credits to {target_id}")
    try:
        bot.send_message(target_id, f"🎉 You received {amount} credits by Owner!")
    except:
        pass

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "Enter your message for broadcast:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    text = message.text
    count = 0
    for uid in users_db.keys():
        try:
            bot.send_message(uid, f"📢 *Broadcast by Owner:*\n\n{text}", parse_mode="Markdown")
            count += 1
        except:
            pass
    bot.reply_to(message, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(commands=['code'])
def make_code(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        code_name = message.text.split()[1]
        msg = bot.reply_to(message, "Enter your amount:")
        bot.register_next_step_handler(msg, process_code_amount, code_name)
    except IndexError:
        bot.reply_to(message, "Usage: /code <PromoWord>")

def process_code_amount(message, code_name):
    amount = int(message.text)
    msg = bot.reply_to(message, "Kitne log ise redeem kar sakte hain? (Enter Max Limit):")
    bot.register_next_step_handler(msg, process_code_limit, code_name, amount)

def process_code_limit(message, code_name, amount):
    limit = int(message.text)
    promos_db[code_name] = {"amount": amount, "limit": limit, "used_by": []}
    bot.reply_to(message, f"✅ Your promo is created successfully!\n\nCode: `{code_name}`\nAmount: {amount}\nMax Users: {limit}")

@bot.message_handler(commands=['expire'])
def expire_code(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        code = message.text.split()[1]
        if code in promos_db:
            del promos_db[code]
            bot.reply_to(message, f"✅ Code {code} successfully expired!")
        else:
            bot.reply_to(message, "❌ Code not found.")
    except IndexError:
        bot.reply_to(message, "Usage: /expire <code>")

# ================= CALLBACK HANDLERS =================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    action = call.data
    
    if user_id not in users_db:
        users_db[user_id] = {"credits": 0, "verified": False}

    if action == "verify_join":
        if is_joined(user_id):
            if not users_db[user_id]["verified"]:
                users_db[user_id]["verified"] = True
                users_db[user_id]["credits"] += 8 
                
                if user_id in pending_referrals:
                    ref_id = pending_referrals[user_id]
                    if ref_id in users_db:
                        users_db[ref_id]["credits"] += 2
                        try:
                            bot.send_message(ref_id, f"🎉 A user joined using your link! You received 2 credits.")
                        except:
                            pass
                    del pending_referrals[user_id]
                
                bot.answer_callback_query(call.id, "✅ Verified! 8 Credits added.", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "Already verified!")
            
            menu_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Please join all channels first!", show_alert=True)
        return

    if not users_db[user_id]["verified"]:
        bot.answer_callback_query(call.id, "❌ Verify channels first!", show_alert=True)
        return

    if action == "check_balance":
        bal = users_db[user_id]["credits"]
        bot.answer_callback_query(call.id, f"💰 Your Balance: {bal} credits", show_alert=True)
        return
        
    if action == "refer_earn":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🔗 *Refer & Earn*\n\nShare this link with friends.\nWhen they start and VERIFY channels, they get 8 credits and YOU get 2 credits!\n\nYour Link: `{ref_link}`"
        bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
        return
        
    if action in ["buy_credit", "buy_api"]:
        bot.send_message(call.message.chat.id, f"🛒 DM Owner to purchase: {OWNER_NAME}")
        return

    if action in PRICES:
        cost = PRICES[action]
        if users_db.get(user_id, {}).get("credits", 0) >= cost:
            msg = bot.send_message(call.message.chat.id, f"✅ Service: {action.replace('_', ' ').title()}\nCost: {cost} Credit\n\n*Enter target data:*", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_lookup, action, cost)
        else:
            bot.answer_callback_query(call.id, f"❌ Need {cost} credits! DM {OWNER_NAME} to buy.", show_alert=True)

# ================= API FETCHING LOGIC =================
def process_lookup(message, action, cost):
    user_id = message.from_user.id
    
    if not message.text:
        bot.send_message(message.chat.id, "❌ Invalid input! Only text is allowed.")
        return

    target = message.text.strip()
    users_db[user_id]["credits"] -= cost
    wait_msg = bot.send_message(message.chat.id, "⏳ Fetching data from server... Please wait.")

    api_result_text = ""
    is_json = False

    try:
        secret_key = API_KEYS[action]
        api_url = f"https://aditya-osint-api.onrender.com/api/v1/info?key={secret_key}&query={target}"
        
        response = requests.get(api_url, timeout=20)
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                api_result_text = json.dumps(json_data, indent=4)
                is_json = True
            except ValueError:
                api_result_text = response.text
        else:
            api_result_text = f"Error: Server responded with code {response.status_code}"

    except Exception:
        api_result_text = f"Error: Server is down or timeout occurred. Try again later."

    bot.delete_message(message.chat.id, wait_msg.message_id)

    # Underscore fix for Markdown formatting
    safe_owner = OWNER_NAME.replace('_', '\\_')
    footer = f"\n\n⚠️ *Note: This message is deleted in 5 minutes.*\nDM to buy credit: {safe_owner}\nDM to buy API: {safe_owner}"
    
    if len(api_result_text) > 3800:
        file_data = io.BytesIO(api_result_text.encode('utf-8'))
        file_data.name = f"{action}_Result.json" if is_json else f"{action}_Result.txt"
        
        sent_msg = bot.send_document(
            message.chat.id, 
            file_data, 
            caption=f"🔍 Data for: `{target}`{footer}", 
            parse_mode="Markdown"
        )
    else:
        if is_json:
            final_text = f"🔍 *Data for:* `{target}`\n\n```json\n{api_result_text}\n```{footer}"
        else:
            final_text = f"🔍 *Data for:* `{target}`\n\n{api_result_text}{footer}"
            
        sent_msg = bot.send_message(message.chat.id, final_text, parse_mode="Markdown")
        
    threading.Timer(300.0, delete_msg, args=[message.chat.id, sent_msg.message_id]).start()

# ================= SETUP CHAT MENU & RUN =================
def setup_menu():
    bot.set_my_commands(
        [
            BotCommand("start", "Start the bot"),
            BotCommand("menu", "Open Main Menu"),
            BotCommand("redeem", "Redeem Promo Code")
        ],
        scope=BotCommandScopeDefault()
    )
    bot.set_my_commands(
        [
            BotCommand("start", "Start the bot"),
            BotCommand("menu", "Open Main Menu"),
            BotCommand("redeem", "Redeem Promo Code"),
            BotCommand("add", "Add Credits (Admin)"),
            BotCommand("broadcast", "Broadcast (Admin)"),
            BotCommand("code", "Create Promo Code (Admin)"),
            BotCommand("expire", "Expire Promo Code (Admin)")
        ],
        scope=BotCommandScopeChat(ADMIN_ID)
    )

print("✅ Setting up UI Menu...")
setup_menu()
print("✅ Bot is online and running perfectly...")

# Updated polling loop without the invalid parameter
try:
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
except Exception as e:
    print(f"Polling crashed: {e}")