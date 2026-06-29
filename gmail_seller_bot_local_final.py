import logging
import os
import psycopg2
import csv
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters,
)
from psycopg2.extras import RealDictCursor

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GMAIL_REWARD = float(os.getenv("GMAIL_REWARD"))
REQUIRED_PASSWORD = os.getenv("REQUIRED_PASSWORD")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_LINK = os.getenv("CHANNEL_LINK")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

(MAIN_MENU, WAITING_GMAIL, WAITING_PASSWORD, WAITING_BINANCE_UID, 
 WAITING_PAYMENT_PROOF, SUPPORT_MESSAGE) = range(6)

# ==================== DATABASE ====================
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY, username TEXT,
        balance REAL DEFAULT 0.0, total_sold INTEGER DEFAULT 0,
        created_at TEXT, state TEXT DEFAULT 'idle')''')
    c.execute('''CREATE TABLE IF NOT EXISTS gmail_submissions (
        id SERIAL PRIMARY KEY, user_id BIGINT,
        gmail TEXT, password TEXT, status TEXT DEFAULT 'pending', created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS withdrawals (
        id SERIAL PRIMARY KEY, user_id BIGINT,
        amount REAL, binance_uid TEXT, status TEXT DEFAULT 'pending',
        admin_accepted INTEGER DEFAULT 0, admin_paid INTEGER DEFAULT 0,
        payment_proof TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id SERIAL PRIMARY KEY, user_id BIGINT,
        username TEXT, message TEXT, status TEXT DEFAULT 'open', created_at TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, balance, total_sold, created_at, state) VALUES (%s, %s, %s, %s, %s)",
                  (user_id, 0.0, 0, datetime.now().isoformat(), 'idle'))
        conn.commit()
        c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = c.fetchone()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_balance(user_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s", (amount, user_id))
    conn.commit()
    conn.close()

def increment_sold(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET total_sold = total_sold + 1 WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

def set_user_state(user_id, state):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET state = %s WHERE user_id = %s", (state, user_id))
    conn.commit()
    conn.close()

def save_gmail_submission(user_id, gmail, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO gmail_submissions (user_id, gmail, password, status, created_at) VALUES (%s, %s, %s, %s, %s)",
              (user_id, gmail, password, 'pending', datetime.now().isoformat()))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid

def is_gmail_duplicate(gmail):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM gmail_submissions WHERE gmail = %s", (gmail,))
    count = c.fetchone()[0]
    conn.close()
    return count > 0

def save_withdrawal(user_id, amount, binance_uid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO withdrawals (user_id, amount, binance_uid, status, created_at) VALUES (%s, %s, %s, %s, %s)",
              (user_id, amount, binance_uid, 'pending', datetime.now().isoformat()))
    wid = c.lastrowid
    conn.commit()
    conn.close()
    return wid

def get_withdrawal(wid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM withdrawals WHERE id=%s", (wid,))
    result = c.fetchone()
    conn.close()
    return result

def accept_withdrawal(wid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET admin_accepted=1 WHERE id=%s", (wid,))
    conn.commit()
    conn.close()

def save_payment_proof(wid, photo_file_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET payment_proof=? WHERE id=%s", (photo_file_id, wid))
    conn.commit()
    conn.close()

def mark_withdrawal_paid(wid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET admin_paid=1, status='completed' WHERE id=%s", (wid,))
    conn.commit()
    conn.close()

def save_support_ticket(user_id, username, message):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO support_tickets (user_id, username, message, created_at) VALUES (%s, %s, %s, %s)",
              (user_id, username, message, datetime.now().isoformat()))
    tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid

def get_support_ticket(tid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM support_tickets WHERE id=%s", (tid,))
    result = c.fetchone()
    conn.close()
    return result

def close_support_ticket(tid):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE support_tickets SET status='closed' WHERE id=%s", (tid,))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, username, total_sold, balance FROM users ORDER BY total_sold DESC LIMIT 10")
    leaders = c.fetchall()
    conn.close()
    return leaders

def get_user_rank(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) + 1 FROM users WHERE total_sold > (SELECT total_sold FROM users WHERE user_id = ?)", (user_id,))
    rank = c.fetchone()[0]
    conn.close()
    return rank

# ==================== EXPORT DATA ====================
def export_to_csv():
    conn = get_conn()
    c = conn.cursor()

    # Export Gmail Sales
    c.execute("SELECT created_at, user_id, gmail, password, status FROM gmail_submissions")
    gmail_data = c.fetchall()

    with open('gmail_sales.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'User ID', 'Gmail', 'Password', 'Status'])
        writer.writerows(gmail_data)

    # Export Withdrawals
    c.execute("SELECT created_at, user_id, amount, binance_uid, status FROM withdrawals")
    withdrawal_data = c.fetchall()

    with open('withdrawals.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'User ID', 'Amount', 'Binance UID', 'Status'])
        writer.writerows(withdrawal_data)

    # Export Users
    c.execute("SELECT user_id, username, balance, total_sold, created_at FROM users")
    users_data = c.fetchall()

    with open('users.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['User ID', 'Username', 'Balance', 'Total Sold', 'Created At'])
        writer.writerows(users_data)

    conn.close()
    return ['gmail_sales.csv', 'withdrawals.csv', 'users.csv']

# ==================== CHANNEL CHECK ====================
async def check_channel_membership(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error("Channel check error: " + str(e))
        return False

# ==================== KEYBOARDS ====================
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Sell Gmail", callback_data="sell_gmail"),
         InlineKeyboardButton("Balance", callback_data="check_balance")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw"),
         InlineKeyboardButton("Support", callback_data="support")],
        [InlineKeyboardButton("Leaderboard", callback_data="leaderboard")],
    ])

def admin_approval_keyboard(sid, uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Approve (+$0.20)", callback_data="approve_" + str(sid) + "_" + str(uid)),
         InlineKeyboardButton("Reject", callback_data="reject_" + str(sid) + "_" + str(uid))],
    ])

def admin_support_reply_keyboard(tid, uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Reply", callback_data="reply_support_" + str(tid) + "_" + str(uid))],
    ])

def admin_accept_keyboard(wid, uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept Request", callback_data="accept_" + str(wid) + "_" + str(uid))],
    ])

def admin_upload_proof_keyboard(wid, uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Upload Payment Proof", callback_data="upload_" + str(wid) + "_" + str(uid))],
    ])

# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    is_member = await check_channel_membership(uid, context)
    if not is_member:
        await update.message.reply_text(
            "You must join our channel to use this bot!\n\n" + CHANNEL_LINK + "\n\nAfter joining, click /start again.")
        return ConversationHandler.END

    get_user(uid)
    set_user_state(uid, 'idle')
    await update.message.reply_text(
        "Welcome " + user.first_name + "!\n\nSell Gmail accounts and earn $0.20 each!\nPassword must be: aass1122\n\nChoose an option:",
        reply_markup=main_menu_keyboard())
    return MAIN_MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    is_member = await check_channel_membership(uid, context)
    if not is_member:
        await query.edit_message_text(
            "You must join our channel!\n\n" + CHANNEL_LINK + "\n\nAfter joining, click /start")
        return ConversationHandler.END

    data = query.data

    if data == "sell_gmail":
        set_user_state(uid, 'waiting_gmail')
        await query.edit_message_text("Please send your Gmail address:\n\nExample: example@gmail.com")
        return WAITING_GMAIL

    elif data == "check_balance":
        user = get_user(uid)
        bal = user[2] if user else 0.0
        rank = get_user_rank(uid)
        await query.edit_message_text(
            "Your Balance\n\nCurrent Balance: $" + "{:.2f}".format(bal) + "\nRank: #" + str(rank) + "\n\nChoose an option:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("Back to Menu", callback_data="back_menu")],
            ]))
        return MAIN_MENU

    elif data == "withdraw":
        user = get_user(uid)
        bal = user[2] if user else 0.0
        if bal < 1.0:
            await query.edit_message_text(
                "Minimum withdrawal is $1.00\nYour balance: $" + "{:.2f}".format(bal) + "\n\nSell more Gmail accounts!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data="back_menu")]]))
            return MAIN_MENU
        set_user_state(uid, 'waiting_binance_uid')
        await query.edit_message_text(
            "Withdrawal Request\n\nYour balance: $" + "{:.2f}".format(bal) + "\n\nPlease send your Binance UID:\nExample: 123456789")
        return WAITING_BINANCE_UID

    elif data == "support":
        set_user_state(uid, 'support')
        await query.edit_message_text(
            "Support Ticket\n\nPlease describe your issue or question:\n\nOr click Back to return.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_menu")]]))
        return SUPPORT_MESSAGE

    elif data == "leaderboard":
        leaders = get_leaderboard()
        text = "Top Sellers Leaderboard\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, leader in enumerate(leaders):
            uid, uname, sold, bal = leader
            text += medals[i] + " @" + str(uname or "Unknown") + " - " + str(sold) + " sold ($" + "{:.2f}".format(bal or 0) + ")\n"

        user = get_user(uid)
        my_rank = get_user_rank(uid)
        text += "\nYour Rank: #" + str(my_rank)

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back to Menu", callback_data="back_menu")]
        ]))
        return MAIN_MENU

    elif data == "back_menu":
        await query.edit_message_text("Welcome back!\n\nChoose an option:", reply_markup=main_menu_keyboard())
        return MAIN_MENU

    return MAIN_MENU

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != ADMIN_ID:
        await query.answer("Not authorized!", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    sid = int(parts[1])
    target = int(parts[2])

    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE gmail_submissions SET status='approved' WHERE id=?", (sid,))
    conn.commit()
    conn.close()

    update_balance(target, GMAIL_REWARD)
    increment_sold(target)

    try:
        await context.bot.send_message(chat_id=target, text="Your Gmail approved! $0.20 added.")
    except: pass
    await query.edit_message_text("Approved! User " + str(target) + " +$0.20")

async def admin_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != ADMIN_ID:
        await query.answer("Not authorized!", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    sid = int(parts[1])
    target = int(parts[2])

    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE gmail_submissions SET status='rejected' WHERE id=?", (sid,))
    conn.commit()
    conn.close()

    try:
        await context.bot.send_message(chat_id=target, text="Your Gmail was rejected. Password must be aass1122")
    except: pass
    await query.edit_message_text("Rejected! User " + str(target))

async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != ADMIN_ID:
        await query.answer("Not authorized!", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    wid = int(parts[1])
    target = int(parts[2])

    withdrawal = get_withdrawal(wid)
    if not withdrawal:
        await query.edit_message_text("Withdrawal not found!")
        return

    amount = withdrawal[2]
    binance_uid = withdrawal[3]
    accept_withdrawal(wid)

    try:
        await context.bot.send_message(
            chat_id=target,
            text="Your withdrawal request has been ACCEPTED!\n\nAmount: $" + "{:.2f}".format(amount) + "\nBinance UID: " + str(binance_uid) + "\n\nPlease wait for payment processing.")
    except Exception as e:
        logging.error("Notify failed: " + str(e))

    await query.edit_message_text(
        "ACCEPTED\n\nUser: " + str(target) + "\nAmount: $" + "{:.2f}".format(amount) + "\nBinance UID: " + str(binance_uid) + "\n\nAfter payment, upload proof photo:",
        reply_markup=admin_upload_proof_keyboard(wid, target))

async def admin_upload_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != ADMIN_ID:
        await query.answer("Not authorized!", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    wid = int(parts[1])
    target = int(parts[2])

    context.user_data['waiting_proof_for'] = wid
    context.user_data['proof_target'] = target

    await query.edit_message_text(
        "Please send the payment proof photo (screenshot of Binance transfer).\n\nSend photo now or /cancel to skip:")
    return WAITING_PAYMENT_PROOF

async def admin_support_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != ADMIN_ID:
        await query.answer("Not authorized!", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    try:
        tid = int(parts[2])
        target = int(parts[3])
    except (IndexError, ValueError):
        await query.answer("Error parsing ticket data!", show_alert=True)
        return

    context.user_data['replying_to_ticket'] = tid
    context.user_data['ticket_user_id'] = target

    await query.edit_message_text(
        "Ticket #" + str(tid) + "\n\nSend your reply message now (or /cancel to skip):")

async def receive_support_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.message.reply_text("Not authorized!")
        return

    tid = context.user_data.get('replying_to_ticket')
    target_user = context.user_data.get('ticket_user_id')

    if not tid or not target_user:
        await update.message.reply_text("No pending reply. Use /tickets to select a ticket.")
        return

    reply_message = update.message.text.strip()
    if reply_message.lower() == "/cancel":
        await update.message.reply_text("Cancelled. No reply sent.")
        context.user_data.pop('replying_to_ticket', None)
        context.user_data.pop('ticket_user_id', None)
        return

    close_support_ticket(tid)

    try:
        await context.bot.send_message(
            chat_id=target_user,
            text="Support Reply to Ticket #" + str(tid) + "\n\nAdmin Response:\n\n" + reply_message)
    except Exception as e:
        logging.error("Reply send failed: " + str(e))
        await update.message.reply_text("Failed to send reply: " + str(e))

    context.user_data.pop('replying_to_ticket', None)
    context.user_data.pop('ticket_user_id', None)

    await update.message.reply_text("Reply sent to user " + str(target_user) + "! Ticket #" + str(tid) + " closed.")

async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.message.reply_text("Not authorized!")
        return MAIN_MENU

    wid = context.user_data.get('waiting_proof_for')
    target = context.user_data.get('proof_target')

    if not wid or not target:
        await update.message.reply_text("No pending payment proof request. Use /stats.")
        return MAIN_MENU

    if not update.message.photo:
        await update.message.reply_text("Please send a photo (screenshot). Or /cancel to skip.")
        return WAITING_PAYMENT_PROOF

    photo = update.message.photo[-1]
    photo_file_id = photo.file_id

    save_payment_proof(wid, photo_file_id)

    withdrawal = get_withdrawal(wid)
    amount = withdrawal[2] if withdrawal else 0
    binance_uid = withdrawal[3] if withdrawal else ""

    deduct_balance(target, amount)
    mark_withdrawal_paid(wid)

    try:
        await context.bot.send_photo(
            chat_id=target,
            photo=photo_file_id,
            caption="PAYMENT COMPLETED!\n\nAmount: $" + "{:.2f}".format(amount) + "\nBinance UID: " + str(binance_uid) + "\n\nPayment proof attached.\nThank you for using our service!"
        )
    except Exception as e:
        logging.error("Photo send failed: " + str(e))
        try:
            await context.bot.send_message(
                chat_id=target,
                text="PAYMENT COMPLETED!\n\nAmount: $" + "{:.2f}".format(amount) + "\nBinance UID: " + str(binance_uid) + "\n\nPayment sent to your Binance account.\nThank you!")
        except: pass

    context.user_data.pop('waiting_proof_for', None)
    context.user_data.pop('proof_target', None)

    await update.message.reply_text("Payment proof sent to user " + str(target) + "! Balance deducted.")
    return MAIN_MENU

async def receive_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    gmail = update.message.text.strip()

    if "@gmail.com" not in gmail and "@googlemail.com" not in gmail:
        await update.message.reply_text("Invalid Gmail. Must be @gmail.com. Try again:")
        return WAITING_GMAIL

    if is_gmail_duplicate(gmail):
        await update.message.reply_text("This Gmail already exists! Try another one:")
        return WAITING_GMAIL

    context.user_data['temp_gmail'] = gmail
    set_user_state(uid, 'waiting_password')
    await update.message.reply_text(
        "Gmail: " + gmail + "\n\nNow send the password.\n\nIMPORTANT: Password must be exactly: aass1122")
    return WAITING_PASSWORD

async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pwd = update.message.text.strip()
    gmail = context.user_data.get('temp_gmail', 'Unknown')
    uname = update.effective_user.username or "Unknown"

    if pwd != REQUIRED_PASSWORD:
        await update.message.reply_text(
            "WRONG PASSWORD!\n\nPassword must be exactly: aass1122\n\nPlease send the password again:")
        return WAITING_PASSWORD

    sid = save_gmail_submission(uid, gmail, pwd)
    set_user_state(uid, 'idle')

    await update.message.reply_text(
        "Your Gmail is under review!\n\nWait for admin approval.", reply_markup=main_menu_keyboard())

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="NEW GMAIL\n\nUser: @" + str(uname) + "\nID: " + str(uid) + "\nGmail: " + str(gmail) + "\nPassword: " + str(pwd) + "\n\nReview:",
            reply_markup=admin_approval_keyboard(sid, uid))
    except Exception as e:
        logging.error("Admin notify failed: " + str(e))
    return MAIN_MENU

async def receive_binance_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    b_uid = update.message.text.strip()
    uname = update.effective_user.username or "Unknown"
    user = get_user(uid)
    bal = user[2] if user else 0.0
    if bal < 1.0:
        await update.message.reply_text("Balance too low.", reply_markup=main_menu_keyboard())
        return MAIN_MENU

    wid = save_withdrawal(uid, bal, b_uid)
    set_user_state(uid, 'idle')

    await update.message.reply_text(
        "Withdrawal submitted!\n\nAmount: $" + "{:.2f}".format(bal) + "\nBinance UID: " + str(b_uid) + "\n\nWait for admin approval.",
        reply_markup=main_menu_keyboard())

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="NEW WITHDRAWAL\n\nUser: @" + str(uname) + "\nID: " + str(uid) + "\nAmount: $" + "{:.2f}".format(bal) + "\nBinance UID: " + str(b_uid) + "\n\nClick Accept:",
            reply_markup=admin_accept_keyboard(wid, uid))
    except Exception as e:
        logging.error("Admin notify failed: " + str(e))
    return MAIN_MENU

async def receive_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    message = update.message.text.strip()
    uname = update.effective_user.username or "Unknown"

    tid = save_support_ticket(uid, uname, message)
    set_user_state(uid, 'idle')

    await update.message.reply_text(
        "Support ticket sent!\n\nWe will reply soon.", reply_markup=main_menu_keyboard())

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text="NEW SUPPORT TICKET #" + str(tid) + "\n\nUser: @" + str(uname) + "\nID: " + str(uid) + "\n\nMessage:\n" + str(message),
            reply_markup=admin_support_reply_keyboard(tid, uid))
    except Exception as e:
        logging.error("Support notify failed: " + str(e))
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    set_user_state(update.effective_user.id, 'idle')
    context.user_data.pop('waiting_proof_for', None)
    context.user_data.pop('proof_target', None)
    await update.message.reply_text("Cancelled.\n\nChoose:", reply_markup=main_menu_keyboard())
    return MAIN_MENU

# ==================== ADMIN COMMANDS ====================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized!")
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gmail_submissions")
    subs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM gmail_submissions WHERE status='pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM withdrawals")
    wds = c.fetchone()[0]
    c.execute("SELECT SUM(balance) FROM users")
    total = c.fetchone()[0] or 0.0
    c.execute("SELECT COUNT(*) FROM support_tickets WHERE status='open'")
    tickets = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(
        "Stats\n\nUsers: " + str(users) + "\nSubmissions: " + str(subs) + "\nPending: " + str(pending) + "\nWithdrawals: " + str(wds) + "\nOpen Tickets: " + str(tickets) + "\nTotal Balance: $" + "{:.2f}".format(total))

async def admin_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized!")
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, user_id, username, message FROM support_tickets WHERE status='open' ORDER BY id DESC")
    tickets = c.fetchall()
    conn.close()

    if not tickets:
        await update.message.reply_text("No open tickets!")
        return

    text = "Open Support Tickets:\n\n"
    for t in tickets:
        tid, uid, uname, msg = t
        text += "#" + str(tid) + " @" + str(uname or "Unknown") + ": " + str(msg[:50]) + "...\n\n"

    await update.message.reply_text(text)

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Not authorized!")
        return

    try:
        files = export_to_csv()
        for file in files:
            await update.message.reply_document(document=open(file, 'rb'))
        await update.message.reply_text("Data exported successfully!\n\nFiles:\n- gmail_sales.csv\n- withdrawals.csv\n- users.csv")
    except Exception as e:
        await update.message.reply_text("Export failed: " + str(e))

async def admin_support_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin's support reply message if they're in reply mode"""
    if context.user_data.get('replying_to_ticket'):
        await receive_support_reply(update, context)
        return ConversationHandler.END
    # If not replying, let the conversation handler take over
    return None

# ==================== MAIN ====================
def main():
    init_db()

    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^approve_"))
    app.add_handler(CallbackQueryHandler(admin_reject, pattern="^reject_"))
    app.add_handler(CallbackQueryHandler(admin_accept, pattern="^accept_"))
    app.add_handler(CallbackQueryHandler(admin_upload_proof, pattern="^upload_"))
    app.add_handler(CallbackQueryHandler(admin_support_reply, pattern="^reply_support_"))
    
    # Message handler for admin support replies (must be before conversation handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_support_reply_message))

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(button_handler)],
            WAITING_GMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_gmail)],
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
            WAITING_BINANCE_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_binance_uid)],
            WAITING_PAYMENT_PROOF: [
                MessageHandler(filters.PHOTO, receive_payment_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_payment_proof)
            ],
            SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("tickets", admin_tickets))
    app.add_handler(CommandHandler("export", admin_export))

    logging.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
