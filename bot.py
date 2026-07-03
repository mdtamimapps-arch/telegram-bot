import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN
from database import *

logging.basicConfig(level=logging.INFO)

# --- কমান্ড হ্যান্ডলার (আগের মতো) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 স্বাগতম!\n\n"
        "📌 কমান্ডসমূহ:\n"
        "/total - মিলের মোট জমা, খরচ ও বাকি\n"
        "/member <নাম> - ওই সদস্যের জমা দেখুন\n"
        "/saif - সাইফের বাসা+ওয়াইফাই+কারেন্টের হিসাব\n"
        "/history - সব খরচের তালিকা\n"
        "/add - নতুন খরচ যোগ করুন"
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

# --- নতুন অংশ: যেকোনো সাধারণ মেসেজের উত্তর দেওয়ার জন্য ---
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 আমি সচল আছি!\n"
        "আমার সাথে কথা বলতে চাইলে নিচের কমান্ডগুলো ব্যবহার করুন:\n"
        "/start - সব কমান্ড দেখুন\n"
        "/total - হিসাব দেখুন"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # কমান্ড হ্যান্ডলার যোগ করুন
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("total", total))
    app.add_handler(CommandHandler("member", member))
    app.add_handler(CommandHandler("saif", saif))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("add", add_expense))
    
    # 💥 নতুন: যেকোনো সাধারণ টেক্সট মেসেজের জন্য হ্যান্ডলার
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("🤖 বট চালু হয়েছে... (এখন যেকোনো মেসেজে সাড়া দেবে)")
    app.run_polling()

if __name__ == "__main__":
    init_data()
    main()