import asyncio
import json
import urllib.request
import urllib.parse
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "9184579325:AAFi1PFbj39vGpyjVa3TQM2Tob_akfE_RsM"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# নিউজ সোর্সগুলো
NEWS_COMMANDS = {
    "/prothomalo": ("প্রথম আলো", "https://news.google.com/rss/search?q=Prothom+Alo&hl=bn&gl=BD&ceid=BD:bn"),
    "/somoy": ("সময় টিভি", "https://news.google.com/rss/search?q=Somoy+TV+news&hl=bn&gl=BD&ceid=BD:bn"),
    "/jamuna": ("যমুনা টেলিভিশন", "https://news.google.com/rss/search?q=Jamuna+TV+news&hl=bn&gl=BD&ceid=BD:bn"),
    "/ekattor": ("একাত্তর টিভি", "https://news.google.com/rss/search?q=Ekattor+TV+news&hl=bn&gl=BD&ceid=BD:bn"),
    "/independent": ("ইন্ডিপেন্ডেন্ট টিভি", "https://news.google.com/rss/search?q=Independent+Television+Bangladesh&hl=bn&gl=BD&ceid=BD:bn"),
    "/channeli": ("চ্যানেল আই", "https://news.google.com/rss/search?q=Channel+i+news&hl=bn&gl=BD&ceid=BD:bn")
}

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHandler)
    server.serve_forever()

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.urlopen(url, timeout=35)
        data = json.loads(req.read().decode('utf-8'))
        if data.get("ok"):
            return data.get("result")
    except Exception as e:
        print(f"Error fetching updates: {e}")
    return []

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    data = urllib.parse.urlencode(payload).encode('utf-8')
    try:
        urllib.request.urlopen(url, data=data)
    except Exception as e:
        print(f"Error sending message: {e}")

async def main():
    print("🤖 Multi-Feature Pure Python Bot is starting...")
    offset = None
    
    threading.Thread(target=run_web_server, daemon=True).start()

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "").strip()
                user_name = message["from"].get("first_name", "User")
                
                if text == "/start":
                    help_text = (
                        f"স্বাগতম, *{user_name}*!\n\n"
                        "🤖 এই বটের মাধ্যমে আপনি লাইভ নিউজ, আবহাওয়া ও নামাজের সময় জানতে পারবেন।\n\n"
                        "📰 *নিউজ কমান্ডসমূহ:*\n"
                        "• /prothomalo - প্রথম আলো\n"
                        "• /somoy - সময় টিভি\n"
                        "• /jamuna - যমুনা টেলিভিশন\n"
                        "• /ekattor - একাত্তর টিভি\n"
                        "• /independent - ইন্ডিপেন্ডেন্ট টিভি\n"
                        "• /channeli - চ্যানেল আই\n\n"
                        "🌤 *অন্যান্য ফিচার:*\n"
                        "• /weather - ঢাকার লাইভ আবহাওয়া\n"
                        "• /prayer - আজকের নামাজের সময়সূচি (ঢাকা)"
                    )
                    send_message(chat_id, help_text)
                    
                elif text in NEWS_COMMANDS:
                    paper_name, feed_url = NEWS_COMMANDS[text]
                    news_text = ""
                    try:
                        req_obj = urllib.request.Request(
                            feed_url,
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                        )
                        req = urllib.request.urlopen(req_obj, timeout=12)
                        xml_data = req.read().decode('utf-8', errors='ignore')
                        
                        items = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)
                        real_title = None
                        real_link = None
                        
                        for item in items:
                            title_match = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                            link_match = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
                            
                            if title_match:
                                t = title_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip()
                                if "Google News" not in t:
                                    real_title = t
                                    if link_match:
                                        real_link = link_match.group(1).strip()
                                    break
                        
                        if real_title:
                            news_text = f"📰 *সর্বশেষ সংবাদ ({paper_name}):*\n\n📌 {real_title}"
                            if real_link:
                                news_text += f"\n\n🔗 [বিস্তারিত পড়তে এখানে ক্লিক করুন]({real_link})"
                        else:
                            news_text = f"❌ এই মুহূর্তে {paper_name}-এর কোনো শিরোনাম পাওয়া যায়নি।"
                    except Exception as e:
                        news_text = f"❌ নিউজ লোড করতে সমস্যা হচ্ছে।"
                        
                    send_message(chat_id, news_text)

                elif text == "/weather":
                    try:
                        # ফ্রি ওয়েদার এপিআই থেকে ঢাকার আবহাওয়া ফেচ করা
                        weather_url = "https://wttr.in/Dhaka?format=j1"
                        req_obj = urllib.request.Request(weather_url, headers={'User-Agent': 'Mozilla/5.0'})
                        req = urllib.request.urlopen(req_obj, timeout=10)
                        w_data = json.loads(req.read().decode('utf-8'))
                        
                        current = w_data['current_condition'][0]
                        temp = current['temp_C']
                        desc = current['lang_bn'][0]['value'] if 'lang_bn' in current else current['weatherDesc'][0]['value']
                        humidity = current['humidity']
                        
                        weather_msg = (
                            f"🌤 *ঢাকার লাইভ আবহাওয়ার আপডেট:*\n\n"
                            f"🌡 তাপমাত্রা: *{temp}°C*\n"
                            f"☁️ অবস্থা: *{desc}*\n"
                            f"💧 আর্দ্রতা: *{humidity}%*"
                        )
                        send_message(chat_id, weather_msg)
                    except Exception:
                        send_message(chat_id, "❌ আবহাওয়া তথ্য লোড করতে সমস্যা হচ্ছে।")

                elif text == "/prayer":
                    try:
                        # ইসলামিক ফাইন্যান্স বা প্রিয়ার টাইম ফ্রি এপিআই (ঢাকা)
                        prayer_url = "http://api.aladhan.com/v1/timingsByCity?city=Dhaka&country=Bangladesh&method=1"
                        req_obj = urllib.request.Request(prayer_url, headers={'User-Agent': 'Mozilla/5.0'})
                        req = urllib.request.urlopen(req_obj, timeout=10)
                        p_data = json.loads(req.read().decode('utf-8'))
                        
                        timings = p_data['data']['timings']
                        prayer_msg = (
                            f"🕌 *আজকের নামাজের সময়সূচি (ঢাকা):*\n\n"
                            f"🌅 ফজর: *{timings['Fajr']}*\n"
                            f"☀️ সূর্যোদয়: *{timings['Sunrise']}*\n"
                            f" 낮 ظہر / যোহর: *{timings['Dhuhr']}*\n"
                            f" عصر / আসর: *{timings['Asr']}*\n"
                            f" 🌆 মাগরিব: *{timings['Maghrib']}*\n"
                            f" 🌙 এশা: *{timings['Isha']}*"
                        )
                        send_message(chat_id, prayer_msg)
                    except Exception:
                        send_message(chat_id, "❌ নামাজের সময়সূচি লোড করতে সমস্যা হচ্ছে।")
                    
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
