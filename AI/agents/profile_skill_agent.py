import os
from pathlib import Path
from sys import path
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)
BASE_DIR=Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)
api_key=os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    raise ValueError("GROQ_API_KEY not found!")

class ProfileSkillAgent:
    def __init__(self):
        self.model=ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.3,
            groq_api_key=api_key
        )
        