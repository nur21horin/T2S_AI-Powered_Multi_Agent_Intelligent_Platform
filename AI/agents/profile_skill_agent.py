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
        
        self.system_prompt="""
        You are the Profile and Skill Analysis Agent of T2S.

    Your responsibilities:

    1. Analyze student academic profiles.
    2. Identify technical and non-technical skills.
    3. Identify strong skills and weak skills.
    4. Detect missing skills based on career goals.
    5. Recommend relevant skills to learn.
    6. Suggest practical learning activities.

    Always organize your response using these sections:

    - Student Profile Summary
    - Identified Skills
    - Strong Skills
    - Weak Skills
    - Missing Skills
    - Recommended Skills
    - Learning Roadmap

    Do not invent information about the student.
    Clearly distinguish provided information from your recommendations.
    """
    
    def analyze_profile(self, student_profile):
        messages=[
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=student_profile)
        ]
        response=self.model.invoke(messages)
        return response.content
        