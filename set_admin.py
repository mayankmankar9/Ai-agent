import firebase_admin
from firebase_admin import credentials, auth

# Path to your service account key
cred = credentials.Certificate("backend/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Replace with the UID of the user you want to make admin
uid = "kR7MY9xQF7XflxLhBjTaFCImBEg1"

# Set admin claim
auth.set_custom_user_claims(uid, { "admin": True })

print(f"✅ Set admin claim for UID: {uid}")
