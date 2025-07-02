from fastapi import HTTPException, Request
from firebase_admin import auth
import app.firebase  # ✅ Ensures Firebase app is initialized

def verify_firebase_token(request: Request):
    authorization: str = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()

        if scheme.lower() != "bearer":
            raise ValueError("Invalid token scheme")

        decoded_token = auth.verify_id_token(token)
        request.state.user = decoded_token  # Optional if needed later
        return decoded_token

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {str(e)}")
