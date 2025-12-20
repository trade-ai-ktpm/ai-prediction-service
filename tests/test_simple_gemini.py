import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

async def test_simple():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"API Key: {api_key[:20]}...")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = "Say 'Hello World' and respond ONLY in JSON format: {\"message\": \"Hello World\"}"
    
    print(f"\nSending prompt: {prompt}\n")
    
    response = await model.generate_content_async(prompt)
    
    print(f"Response text: {response.text}")
    print(f"\nResponse object: {response}")

if __name__ == "__main__":
    asyncio.run(test_simple())
