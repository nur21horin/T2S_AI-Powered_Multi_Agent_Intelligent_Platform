import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)

# Load environment variables
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)

api_key = os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    raise ValueError("GROQ_API_KEY not found!")

print("Groq API key loaded:", bool(api_key))

# Initialize Groq LLM
model = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0.7,
    groq_api_key=api_key
)

# Conversation history
messages = [
    SystemMessage(
        content="You are a helpful, intelligent and friendly AI assistant."
    )
]

print("\n---------- Groq AI Chatbot ----------")
print("Type 0 to exit.")

while True:

    prompt = input("\nYou: ").strip()

    if prompt == "0":
        print("Goodbye!")
        break

    if not prompt:
        continue

    messages.append(HumanMessage(content=prompt))

    try:
        response = model.invoke(messages)

        messages.append(AIMessage(content=response.content))

        print("\nBot:", response.content)

    except Exception as e:
        messages.pop()
        print("\nError:", str(e))