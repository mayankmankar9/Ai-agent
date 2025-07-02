from firebase_admin import credentials, firestore, initialize_app

# Initialize Firebase
cred = credentials.Certificate("backend/serviceAccountKey.json")
initialize_app(cred)

db = firestore.client()

# 🔐 Replace with the same UID used above
uid = "kR7MY9xQF7XflxLhBjTaFCImBEg1"

plan_data = {
    "Monday": "Oats + protein shake, tofu curry + rice, dal + roti",
    "Tuesday": "Smoothie, paneer wrap, rajma + brown rice",
    "summary": "Vegetarian cutting plan with 2000 kcal and 120g protein/day"
}

# Save to: users/<uid>/plans/generated
db.collection("users").document(uid).collection("plans").document("generated").set(plan_data)

print("✅ Plan saved to Firestore.")
