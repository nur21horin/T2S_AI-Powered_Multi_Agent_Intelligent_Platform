from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
from AI.agents.profile_skill_agent import ProfileSkillAgent
app = FastAPI(title="T2S AI-Powered Multi-Agent Intelligent Platform", description="An AI-powered multi-agent intelligent platform for student profile and skill analysis.", version="1.0.0")

#Frontend CORS configuration

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Initialize the ProfileSkillAgent
profile_skill_agent = ProfileSkillAgent()

class StudentProfileRequest(BaseModel):
    student_profile: str
    
@app.get("/")
def home():
    return {"message": "Welcome to the T2S AI-Powered Multi-Agent Intelligent Platform API!"}
@app.post("/api/agents/profile-skill-analysis")
def analyze_profile(data:StudentProfileRequest):
    try:
        result=profile_skill_agent.analyze_profile(data.student_profile)
        return{
            "success":True,
            "agent":"Profile & Skill Agent",
            "result":result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    