import os
from dotenv import load_dotenv

print("====================================================")
print("   💠 MODERN GEMINI API TEST (NEW GOOGLE-GENAI)     ")
print("====================================================")

# ۱. بارگذاری فایل .env
load_dotenv()

# ۲. پاکسازی تداخل‌های قدیمی
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

try:
    # ۳. وارد کردن کتابخانه جدید گوگل (نسخه استاندارد کنونی)
    from google import genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Loaded Key: {api_key[:5]}...{api_key[-4:]}")
    
    print("⏳ Connecting to Google Servers using new client architecture...")
    
    # ۴. ساخت کلاینت بر اساس ساختار جدید گوگل (کلید AQ بدون هیچ مشکلی اینجا پذیرفته می‌شود)
    client = genai.Client(api_key=api_key)
    
    # ۵. ارسال درخواست به مدل استاندارد
    response = client.models.generate_content(
        model='gemini-2.5-flash', # مطابق لاگ شما که از نسخه ۲.۵ استفاده می‌کند
        contents='Hello Gemini! Confirm connection by saying "API IS LIVE AND ACTIVE".'
    )
    
    print("\n====================================================")
    print("🎉 🎉 🎉 SUCCESS! API IS FULLY OPERATIONAL 🎉 🎉 🎉")
    print("====================================================")
    print(f"Gemini Response: {response.text.strip()}")
    print("====================================================")

except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print(f"⚠️ Error Details: {str(e)}")
    print("====================================================")