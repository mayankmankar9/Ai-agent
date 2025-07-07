from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agent_runner import run_agent
from app.firebase import get_user_profile, save_user_profile, get_weekly_plans

app = FastAPI(title="AI Nutrition Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserProfile(BaseModel):
    goal: str
    goal_intensity: str = "balanced"
    diet_type: str
    dislikes: str = ""
    weight_kg: float
    height_cm: float
    age: int
    gender: str
    activity_level: Literal["sedentary", "moderate", "very active"]
    tenure_months: int = 3
    target_weight: float

class AgentQuery(BaseModel):
    user_id: str
    query: str

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/", response_model=HealthResponse)
def read_root():
    return {"status": "healthy", "message": "AI Nutrition Agent API is running"}

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "healthy", "message": "Backend is operational"}

@app.get("/user/{user_id}")
def get_user(user_id: str):
    try:
        user_profile = get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User not found")
        return user_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.post("/user/{user_id}")
def save_user(user_id: str, profile: UserProfile):
    try:
        save_user_profile(user_id, profile.dict())
        return {"message": "User profile saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving user: {str(e)}")

@app.post("/agent/query")
def agent_query(request: AgentQuery):
    try:
        result = run_agent(request.user_id, request.query)
        return {"response": result}
    except Exception as e:
        print("ERROR in /agent/query:", e)
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running agent: {str(e)}")

@app.get("/plans/{user_id}")
def get_plans(user_id: str):
    try:
        plans = get_weekly_plans(user_id)
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching plans: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
