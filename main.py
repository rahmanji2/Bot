import asyncio
import logging
import random
import feedparser
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, add_giveaway_user, get_random_winner

BOT_TOKEN = "9184579325:AAFi1PFbj39vGpyjVa3TQM2Tob_akfE_RsM"
CHANNEL_LINK = "https://t.me/teesdfa"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Join Giveaway", callback_data="menu_giveaway")],
        [InlineKeyboardButton(text="📰 Latest News (বাংলা)", callback_data="menu_news")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    init_db()
    welcome_text = (
        f"স্বাগতম, **{message.from_user.first_name}**!\n\n"
        "এটি আপনার অল-ইন-ওয়ান মাল্টি-পারপাস বট। নিচে থেকে আপনার পছন্দের ফিচার সিলেক্ট করুন:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "মূল মেনুতে ফিরে এসেছেন:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_giveaway")
async def join_giveaway(callback: types.CallbackQuery):
    user = callback.from_user
    success = add_giveaway_user(user.id, user.username or user.first_name)
    
    if success:
        text = "🎉 অভিনন্দন! সফলভাবে গিভঅ্যাওয়েতে আপনার নাম এন্ট্রি করা হয়েছে।"
    else:
        text = "ℹ️ আপনি ইতিমধ্যে এই গিভঅ্যাওয়েতে জয়েন করে আছেন!"
        
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মেনুতে ফিরে যান", callback_data="back_home")]
    ])
    await callback.message.edit_text(text, reply_markup=back_kb)
    await callback.answer()

@dp.message(Command("picker"))
async def pick_winner(message: types.Message):
    winner = get_random_winner()
    if winner:
        user_id, username = winner
        name_display = f"@{username}" if username else f"ID: {user_id}"
        await message.answer(f"🏆 **গিভঅ্যাওয়ে উইনার:** {name_display} (`{user_id}`)!", parse_mode="Markdown")
    else:
        await message.answer("❌ গিভঅ্যাওয়েতে এখনও কেউ জয়েন করেনি!")

@dp.callback_query(F.data == "menu_news")
async def fetch_latest_news(callback: types.CallbackQuery):
    await callback.message.edit_text("📰 লেটেস্ট বাংলা নিউজ সংগ্রহ করা হচ্ছে, একটু অপেক্ষা করুন...")
    
    rss_feeds = [
        "https://www.prothomalo.com/feed/",
        "https://www.jugantor.com/feed/",
        "https://www.kalerkantho.com/rss.xml"
    ]
    
    news_list = []
    for url in rss_feeds:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                entry = feed.entries[0]
                news_list.append(f"📌 **{entry.title}**\n🔗 [বিস্তারিত পড়ুন]({entry.link})")
        except Exception:
            continue
            
    if news_list:
        news_text = "📰 **সর্বশেষ বাংলা সংবাদ:**\n\n" + "\n\n".join(news_list[:4])
    else:
        news_text = "❌ দুঃখিত, এই মুহূর্তে নিউজ ফেচ করা সম্ভব হচ্ছে না।"
        
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মেনুতে ফিরে যান", callback_data="back_home")]
    ])
    
    await callback.message.edit_text(news_text, reply_markup=back_kb, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

async def main():
    init_db()
    print("🤖 Bot is starting successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
