from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask, daemon=True).start()

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN
from database import *

logging.basicConfig(level=logging.INFO)

# ---------- পুরোনো কমান্ড ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 স্বাগতম!\n\n"
        "📌 কমান্ডসমূহ:\n"
        "/total - মিলের মোট জমা, খরচ ও বাকি\n"
        "/member <নাম> - ওই সদস্যের জমা দেখুন\n"
        "/saif - সাইফের বাসা+ওয়াইফাই+কারেন্টের হিসাব\n"
        "/history - সব খরচের তালিকা\n"
        "/add - নতুন খরচ যোগ করুন\n\n"
        "👤 সদস্য প্রোফাইল (ইংরেজি কমান্ড):\n"
        "/akash, /pranto, /samiul, /tamim, /mehedi, /saif, /samy, /lalon"
    )

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_deposit = get_total_deposit()
    total_expense = get_total_expenses()
    balance = total_deposit - total_expense
    
    msg = f"📊 **মিলের হিসাব**\n\n"
    msg += f"💰 মোট জমা: {total_deposit} টাকা\n"
    msg += f"🛒 মোট খরচ: {total_expense} টাকা\n"
    msg += f"✅ বাকি: {balance} টাকা\n\n"
    msg += "👤 সদস্যদের জমা:\n"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT name, deposit FROM members ORDER BY name')
    rows = cursor.fetchall()
    for name, deposit in rows:
        msg += f"• {name}: {deposit} টাকা\n"
    conn.close()
    
    await update.message.reply_text(msg)

async def member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ নাম দিন: /member আকাশ")
        return
    name = ' '.join(context.args)
    deposit = get_member_deposit(name)
    if deposit == 0 and name not in ['আকাশ','প্রান্ত','সামিউল','তামীম','মেহেদী','সাইফ','সাম্য','লালন']:
        await update.message.reply_text(f"❌ '{name}' নামে কোনো সদস্য নেই।")
    else:
        await update.message.reply_text(f"👤 {name}\n💰 জমা: {deposit} টাকা")

async def saif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_special_expense('সাইফ')
    if data:
        amount, category = data
        await update.message.reply_text(f"🏠 সাইফের আলাদা জমা:\n{category}: {amount} টাকা")
    else:
        await update.message.reply_text("❌ কোনো ডেটা নেই।")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = get_all_expenses()
    if not rows:
        await update.message.reply_text("📭 এখনও কোনো খরচ নেই।")
        return
    
    msg = "📜 **সব খরচের তালিকা**:\n\n"
    for date, desc, paid, amount in rows:
        msg += f"📅 {date} | {desc} | {paid} | {amount} টাকা\n"
    await update.message.reply_text(msg)

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text(
            "ফরম্যাট: /add তারিখ বিবরণ কে কিনেছে টাকা\n"
            "যেমন: /add 2026-07-02 চাল তামীম 500"
        )
        return
    
    date = context.args[0]
    desc = context.args[1]
    paid_by = context.args[2]
    try:
        amount = int(context.args[3])
    except:
        await update.message.reply_text("❌ টাকা সংখ্যা হতে হবে।")
        return
    
    add_new_expense(date, desc, paid_by, amount)
    await update.message.reply_text(f"✅ খরচ যোগ করা হয়েছে:\n{date} | {desc} | {paid_by} | {amount} টাকা")

# ---------- প্রোফাইল জেনারেটর ----------
def generate_profile(name):
    deposit = get_member_deposit(name)
    bills = get_member_bills(name)
    expenses = get_member_expenses(name)
    
    msg = f"👤 **{name}**\n"
    msg += f"💰 মিলে জমা: {deposit} টাকা\n\n"
    
    msg += "📋 **বিলের বিবরণ (জুলাই ২০২৬):**\n"
    total_bill = 0
    total_paid = 0
    for bill_type, amount, paid, paid_by in bills:
        status = "✅ পরিশোধ করেছেন" if paid else "❌ বাকি"
        if paid:
            total_paid += amount
            if paid_by:
                status += f" (দিয়েছেন: {paid_by})"
        total_bill += amount
        msg += f"• {bill_type}: {amount} টাকা — {status}\n"
    
    msg += f"\n📊 **বিলের সারাংশ:**\n"
    msg += f"মোট বিল: {total_bill} টাকা\n"
    msg += f"পরিশোধ করেছেন: {total_paid} টাকা\n"
    msg += f"বাকি: {total_bill - total_paid} টাকা\n\n"
    
    if expenses:
        msg += "🛒 **মিলের খরচ (এই সদস্য দিয়েছেন):**\n"
        for date, desc, amount in expenses:
            msg += f"• {date} | {desc} | {amount} টাকা\n"
    else:
        msg += "🛒 মিলের কোনো খরচ করেননি।\n"
    
    special = get_special_expense(name)
    if special:
        s_amount, s_cat = special
        msg += f"\n🏠 **বিশেষ জমা:**\n{s_cat}: {s_amount} টাকা\n"
    
    return msg

# ---------- ৮টি প্রোফাইল কমান্ড (ইংরেজি) ----------
async def profile_akash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('আকাশ'))

async def profile_pranto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('প্রান্ত'))

async def profile_samiul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('সামিউল'))

async def profile_tamim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('তামীম'))

async def profile_mehedi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('মেহেদী'))

async def profile_saif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('সাইফ'))

async def profile_samy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('সাম্য'))

async def profile_lalon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(generate_profile('লালন'))

# ---------- সাধারণ মেসেজের উত্তর ----------
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 আমি সচল আছি!\n"
        "আমার সাথে কথা বলতে চাইলে নিচের কমান্ডগুলো ব্যবহার করুন:\n"
        "/start - সব কমান্ড দেখুন\n"
        "/total - হিসাব দেখুন"
    )

def main():
    bot_app = Application.builder().token(BOT_TOKEN).build()
    
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("total", total))
    bot_app.add_handler(CommandHandler("member", member))
    bot_app.add_handler(CommandHandler("saif", saif))
    bot_app.add_handler(CommandHandler("history", history))
    bot_app.add_handler(CommandHandler("add", add_expense))
    
    # ইংরেজি কমান্ড (বাংলায় প্রোফাইল দেখাবে)
    bot_app.add_handler(CommandHandler("akash", profile_akash))
    bot_app.add_handler(CommandHandler("pranto", profile_pranto))
    bot_app.add_handler(CommandHandler("samiul", profile_samiul))
    bot_app.add_handler(CommandHandler("tamim", profile_tamim))
    bot_app.add_handler(CommandHandler("mehedi", profile_mehedi))
    bot_app.add_handler(CommandHandler("saif", profile_saif))
    bot_app.add_handler(CommandHandler("samy", profile_samy))
    bot_app.add_handler(CommandHandler("lalon", profile_lalon))
    
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("🤖 বট চালু হয়েছে... (সব ফিচারসহ)")
    bot_app.run_polling()

if __name__ == "__main__":
    init_data()
    main()
