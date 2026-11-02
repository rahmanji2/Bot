import asyncio
import json
import urllib.request
import urllib.parse
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BOT_TOKEN = "9184579325:AAFi1PFbj39vGpyjVa3TQM2Tob_akfE_RsM"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

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

def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    data = urllib.parse.urlencode(payload).encode('utf-8')
    try:
        urllib.request.urlopen(url, data=data)
    except Exception as e:
        print(f"Error sending message: {e}")

async def main():
    print("🤖 Pure Python Bot is starting...")
    offset = None
    
    # ব্যাকগ্রাউন্ডে ডামি ওয়েব সার্ভার রান করা (প্যানেল লাইভ রাখার জন্য)
    threading.Thread(target=run_web_server, daemon=True).start()

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "")
                user_name = message["from"].get("first_name", "User")
                
                if text == "/start":
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🎁 Join Giveaway", "callback_data": "giveaway"}],
                            [{"text": "📰 Latest News", "callback_data": "news"}]
                        ]
                    }
                    welcome_text = f"স্বাগতম, *{user_name}*!\n\nএটি আপনার অল-ইন-ওয়ান বট। নিচের অপশন থেকে সিলেক্ট করুন:"
                    send_message(chat_id, welcome_text, json.dumps(keyboard))
                    
            elif "callback_query" in update:
                callback = update["callback_query"]
                chat_id = callback["message"]["chat"]["id"]
                data = callback["data"]
                
                if data == "giveaway":
                    send_message(chat_id, "🎉 অভিনন্দন! সফলভাবে গিভঅ্যাওয়েতে আপনার নাম এন্ট্রি করা হয়েছে।")
                elif data == "news":
                    try:
                        req_obj = urllib.request.Request(
                            "https://www.prothomalo.com/feed/",
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                        )
                        req = urllib.request.urlopen(req_obj, timeout=10)
                        xml_data = req.read().decode('utf-8')
                        
                        titles = re.findall(r'<item>.*?<title>(.*?)</title>.*?</item>', xml_data, re.DOTALL)
                        
                        if titles:
                            news_title = titles[0].replace('<![CDATA[', '').replace(']]>', '').strip()
                            news_text = f"📰 *সর্বশেষ সংবাদ (প্রথম আলো):*\n\n📌 {news_title}"
                        else:
                            news_text = "❌ এই মুহূর্তে কোনো সংবাদ পাওয়া যায়নি।"
                    except Exception as e:
                        news_text = f"❌ নিউজ লোড করতে সমস্যা হচ্ছে।"
                        
                    send_message(chat_id, news_text)
                    
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
