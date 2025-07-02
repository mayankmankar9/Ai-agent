from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.agent_runner import run_agent
from app.deps.firebase_auth import verify_firebase_token
from app.firebase import save_weekly_plan  # ✅ Add this import

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask_agent(request: Request, user=Depends(verify_firebase_token)):
    data = await request.json()
    uid = user["uid"]
    query = data.get("query")

    # ✅ Call LangChain agent logic
    result = run_agent(uid, query)

    # ✅ Save the generated plan to Firestore with timestamp
    save_weekly_plan(uid, result)

    return {"response": result}
