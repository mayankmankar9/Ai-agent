import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

# Compute absolute path to serviceAccountKey.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)

# ✅ Initialize Firebase once
if not firebase_admin._apps:
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

# ✅ Updated 🔹 Save detailed weekly plan data with logging
def save_weekly_plan(
    user_id: str,
    week_number: int,
    start_weight: float,
    end_weight: float,
    calories: float,
    protein: float,
    carbs: float,
    fat: float,
    warnings: list[str],
    response: str,
    meals: list = None  # List of meal names/IDs for duplicate checking
):
    db = firestore.client()
    try:
        print(f"📥 Attempting to save week {week_number} for user {user_id}...")
        doc_ref = (
            db.collection("users")
              .document(user_id)
              .collection("plans")
              .document(f"week_{week_number}")
        )
        doc_ref.set(
            {
                "week_number": week_number,
                "start_weight": start_weight,
                "end_weight": end_weight,
                "calories": calories,
                "protein": protein,
                "carbs": carbs,
                "fat": fat,
                "warnings": warnings,
                "response": response,
                "meals": meals or [],
                "generated_at": firestore.SERVER_TIMESTAMP,
            }
        )
        print(f"✅ Successfully saved week {week_number} for user {user_id}")
    except Exception as e:
        print(f"❌ Error while saving week {week_number} for user {user_id}: {e}")

# 🔹 Fetch weekly plans for a user (ordered by week_number)
def get_weekly_plans(user_id: str):
    db = firestore.client()
    plans_ref = db.collection("users").document(user_id).collection("plans")
    docs = plans_ref.order_by("week_number").stream()
    return [doc.to_dict() for doc in docs]
