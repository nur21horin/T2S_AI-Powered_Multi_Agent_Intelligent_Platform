from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
from AI.agents.profile_skill_agent import ProfileSkillAgent
app = FastAPI(title="T2S AI-Powered Multi-Agent Intelligent Platform", description="An AI-powered multi-agent intelligent platform for student profile and skill analysis.", version="1.0.0")
