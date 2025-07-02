from firebase_admin import credentials, firestore, initialize_app

# Initialize Firebase app only once
cred = credentials.Certificate("backend/serviceAccountKey.json")
initialize_app(cred)

db = firestore.client()

# 🔍 Replace with a real Firebase UID (already logged in from frontend)
uid = "kR7MY9xQF7XflxLhBjTaFCImBEg1"  # your actual Firebase Auth UID

doc = db.collection("users").document(uid).get()
if doc.exists:
    print("✅ User profile found:")
    print(doc.to_dict())
else:
    print("❌ User profile not found.")
