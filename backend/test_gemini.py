
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Gemini API key not found in .env")
else:
    try:
        client = genai.Client(api_key=api_key)

        print("Testing Gemini API...")

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Hello Gemini! Test connection."
        )

        print("Gemini API Connected Successfully!")
        print(response.text)

    except Exception as e:
        print("Gemini API Error:")
        print(type(e).__name__)
        print(str(e))
