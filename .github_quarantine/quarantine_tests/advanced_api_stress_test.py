import os
import time
from google import genai
from dotenv import load_dotenv

# ۱. بارگذاری فایل .env و پاکسازی تداخل‌های سیستم
load_dotenv()
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

print("====================================================")
print("   💠 FORCING GEMINI TO ACCEPT NEW 'AQ.' API KEY     ")
print("====================================================")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ API Key is missing in .env")
    exit(1)

try:
    print(f"Detected Key Format: {api_key[:5]}...")
    
    # ۲. ترفند اصلی: استفاده از کلاینت جدید گوگل برای کلیدهای AQ
    client = genai.Client(api_key=api_key)
    
    print("⏳ Sending live request to Gemini using your funded account...")
    start_time = time.time()
    
    # یک درخواست ساده برای تست سلامت ارتباط
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Verify connection. Reply with exactly: 'API AUTH SUCCESSFUL'."
    )
    elapsed = (time.time() - start_time) * 1000
    
    print(f"\n✅ [SUCCESS] Connection established in {elapsed:.0f}ms!")
    print(f"💬 Gemini Response: {response.text.strip()}")
    print("====================================================")
    print("عالی شد! حالا فرمت جدید کلید کاملاً توسط پایتون شناخته شد.")

except Exception as e:
    print("\n❌ [STILL FAILING] Connection blocked.")
    print(f"⚠️ Details: {str(e)}")
    print("====================================================")