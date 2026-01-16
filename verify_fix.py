from app.gemini_analysis import GeminiAnalyzer
import os
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    try:
        analyzer = GeminiAnalyzer()
        # Asking in English but expecting Hindi
        print("Testing Hindi Translation...")
        response = analyzer.chat_response("What is Aadhaar?", context="Test context", language='hi')
        print("Success!")
        print("-" * 50)
        print("Response Snippet (Should be Hindi):")
        print(response[:500])
        print("-" * 50)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_gemini()
