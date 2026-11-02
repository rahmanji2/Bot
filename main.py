import asyncio
import logging
import requests
import random
import feedparser
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import init_db, add_giveaway_user, get_random_winner

# বটের তথ্য
BOT_TOKEN = "9184579325:AAFi1PFbj39vGpyjVa3TQM2Tob_akfE_RsM"
CHANNEL_LINK = "https://t.me/teesdfa"

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# স্টেট মেশিন (IP/Domain ইনপুট নেওয়ার জন্য)
class LookupState(StatesGroup):
    waiting_for_query = State()

# --- প্রধান মেনু কিবোর্ড ---
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 IP & Domain Lookup", callback_data="menu_lookup")],
        [InlineKeyboardButton(text="🎁 Join Giveaway", callback_data="menu_giveaway")],
        [InlineKeyboardButton(text="📰 Latest News (বাংলা)", callback_data="menu_news")]
    ])
    return keyboard

# /start কমান্ড
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    init_db()
    welcome_text = (
        f"স্বাগতম, **{message.from_user.first_name}**!\n\n"
        "এটি আপনার অল-ইন-ওয়ান মাল্টি-পারপাস বট। নিচে থেকে আপনার পছন্দের ফিচার সিলেক্ট করুন:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

# হোম বাটনে ফেরার হ্যান্ডেলার
@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "মূল মেনুতে ফিরে এসেছেন:",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# ==================== ১. IP & Domain Lookup ফিচার ====================
@dp.callback_query(F.data == "menu_lookup")
async def ask_lookup_query(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "দয়া করে যে কোনো **IP Address** অথবা **Domain Name** (যেমন: `google.com` বা `8.8.8.8`) লিখে পাঠান:",
        parse_mode="Markdown"
    )
    await state.set_state(LookupState.waiting_for_query)
    await callback.answer()

@dp.message(LookupState.waiting_for_query)
async def process_lookup(message: types.Message, state: FSMContext):
    query = message.text.strip()
    await message.answer(f"⏳ `{query}` এর তথ্য খোঁজা হচ্ছে...", parse_mode="Markdown")
    
    try:
        response = requests.get(f"http://ip-api.com/json/{query}", timeout=10)
        data = response.json()
        
        if data.get("status") == "success":
            result = (
                f"🌐 **Lookup Result for:** `{query}`\n\n"
                f"📌 **IP:** `{data.get('query')}`\n"
                f"🌍 **Country:** {data.get('country')} ({data.get('countryCode')})\n"
                f"🏙️ **City:** {data.get('city')}\n"
                f"🏢 **ISP:** {data.get('isp')}\n"
                f"📡 **Org:** {data.get('org')}\n"
            )
        else:
            result = f"❌ দুঃখিত, `{query}` এর কোনো সঠিক তথ্য পাওয়া যায়নি।"
    except Exception as e:
        result = f"⚠️ ত্রুটি হয়েছে: {str(e)}"
        
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 মেনুতে ফিরে যান", callback_data="back_home")]
    ])
    
    await message.answer(result, reply_markup=back_kb, parse_mode="Markdown")
    await state.clear()


# ==================== ২. Giveaway ফিচার ====================
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

# উইনার সিলেক্ট করার সিক্রেট কমান্ড (/picker)
@dp.message(Command("picker"))
async def pick_winner(message: types.Message):
    winner = get_random_winner()
    if winner:
        user_id, username = winner
        name_display = f"@{username}" if username else f"ID: {user_id}"
        await message.answer(f"🏆 **গিভঅ্যাওয়ে উইনার:** {name_display} (`{user_id}`)!", parse_mode="Markdown")
    else:
        await message.answer("❌ গিভঅ্যাওয়েতে এখনও কেউ জয়েন করেনি!")


# ==================== ৩. News Scraper ফিচার (বাংলা নিউজপেপার) ====================
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


# ==================== মেইন রান ফাংশন ====================
async def main():
    init_db()
    print("🤖 Bot is starting successfully...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
