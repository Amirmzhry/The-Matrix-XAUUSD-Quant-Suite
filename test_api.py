import os
from src.core.llm_client import call_gemini

def run_test():
    print("====================================")
    print("🤖 GEMINI API CONNECTION TEST 🤖")
    print("====================================\n")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY is not set in the environment.")
        print("Make sure your .env file exists and contains the key.")
        return
        
    print(f"✅ Found API Key starting with: {api_key[:10]}...\n")
    
    try:
        print("⏳ Connecting to Google Gemini API (gemini-2.5-flash)...")
        # llm_client.py initializes the client seamlessly
        response_text = call_gemini(
            prompt="System: You are a connection tester.\nUser: Respond with exactly one word: SUCCESS"
        )
        print(f"\n✅ Connection Successful!")
        print(f"🤖 Gemini says: {response_text.strip()}\n")
    except Exception as e:
        print(f"\n❌ Connection Failed: {e}")

if __name__ == "__main__":
    run_test()
