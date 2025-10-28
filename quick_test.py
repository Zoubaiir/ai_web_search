"""Quick OpenAI test using your API key from .env"""
from dotenv import load_dotenv
import os
from openai import OpenAI

def main():
    load_dotenv()
    client = OpenAI()
    
    print("Sending request to OpenAI...")
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Write a brief thank you email. Return only plain text.",
        tools=[{"type": "text"}]
    )
    
    if hasattr(response, "output"):
        for item in response.output:
            if hasattr(item, "type") and item.type == "message":
                for content in item.content:
                    if hasattr(content, "text"):
                        print("\nGENERATED EMAIL:\n")
                        print(content.text)
                        return

if __name__ == "__main__":
    main()
