import requests
import firebase_admin
from firebase_admin import credentials, auth

# -----------------------------
# STEP 1: Initialize Firebase Admin SDK
# -----------------------------
cred = credentials.Certificate("backend/serviceAccountKey.json")

# Prevent re-initialization if already initialized
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# -----------------------------
# STEP 2: Generate a custom token and simulate user sign-in
# -----------------------------

# Replace this with a real Firebase user ID from your project
uid = "kR7MY9xQF7XflxLhBjTaFCImBEg1"  # ✅ Use a real UID from Firebase Auth

# Firebase Web API key from frontend config (firebase.ts)
FIREBASE_WEB_API_KEY = "AIzaSyBb_rxMq1ijhfV05LT6jRPSa81yUZ_hrc8"

# Create a custom token for the user
custom_token = auth.create_custom_token(uid).decode("utf-8")

# Exchange the custom token for an ID token via Firebase REST API
firebase_response = requests.post(
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_WEB_API_KEY}",
    json={"token": custom_token, "returnSecureToken": True}
)

# Extract the ID token
id_token = firebase_response.json().get("idToken")

if not id_token:
    print("❌ Failed to get Firebase ID token. Response:")
    print(firebase_response.json())
    exit()

# -----------------------------
# STEP 3: Test the FastAPI endpoint
# -----------------------------
headers = {
    "Authorization": f"Bearer {id_token}"
}

payload = {
    "query": "Create a high-protein non-vegetarian diet plan for bulking"
}

response = requests.post("http://localhost:8000/ask", json=payload, headers=headers)

print("✅ Agent Response:")
print(response.json())
