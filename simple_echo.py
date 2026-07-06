print("--- STARTING ISOLATED ECHO TEST ---")
import os
print("1. Python basic modules loaded.")

try:
    import google.generativeai as genai
    print("2. Google Generative AI library loaded successfully.")
except ImportError:
    print("2. ❌ Library NOT installed. Run: pip install google-generativeai")
    exit()

# کلید خود را اینجا به صورت دستی و مستقیم کپی کنید
MY_KEY = "AIzaSy..." 

print(f"3. Configuring API with Key: {MY_KEY[:8]}...")
genai.configure(api_key=MY_KEY)
print("4. Configuration passed.")

try:
    print("5. Sending light payload to Gemini...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say Hello")
    print(f"🎉 SUCCESS! Gemini responded: {response.text.strip()}")
except Exception as e:
    print(f"❌ CRASHED during call: {e}")