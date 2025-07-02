import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# ✅ Initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")  # Adjust if needed
    firebase_admin.initialize_app(cred)

# 🔹 Get complete user profile
def get_user_profile(user_id: str):
    db = firestore.client()
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    return {}

# 🔹 Get used foods for weekly planner
def get_used_foods(user_id: str):
    db = firestore.client()
    doc = db.collection("users").document(user_id).collection("plans").document("used_foods").get()
    if doc.exists:
        return doc.to_dict().get("foods", [])
    return []

# 🔹 Update used foods to avoid repetition
def update_used_foods(user_id: str, foods: list):
    db = firestore.client()
    db.collection("users").document(user_id).collection("plans").document("used_foods").set({
        "foods": foods
    })

# 🔹 Save or update user profile (used for POST /save-user or form)
def save_user_profile(user_id: str, data: dict):
    db = firestore.client()
    db.collection("users").document(user_id).set(data, merge=True)

def save_weekly_plan(user_id: str, response_text: str):
    db = firestore.client()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    db.collection("users").document(user_id).collection("plans").document(timestamp).set({
        "plan": response_text,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    