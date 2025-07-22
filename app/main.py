from datetime import datetime, timedelta
import time
from fastapi import FastAPI, Header, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse
from app.auth import get_auth_url, get_token_by_auth_code, refresh_access_token
from app.graph_api import create_event, update_event, delete_event
from app.models import EventRequest
from typing import Optional

from sqlalchemy.orm import Session
from app.db import Token
from app.db import get_db
from app.services import get_email_from_id_token

app = FastAPI()
token_store = {}
  # In production, use a DB or encrypted store
EXPIRATION_BUFFER_SECONDS = 300


@app.get("/")
def root():
    return {"message": "Microsoft Calendar Integration using FastAPI"}

@app.get("/auth/login")
def login():
    auth_url = get_auth_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing auth code")

    result = get_token_by_auth_code(code)
    if "access_token" not in result:
        raise HTTPException(status_code=400, detail="Authentication failed")

    # Get user's email from the ID token
    id_token = result.get("id_token")
    email = get_email_from_id_token(id_token)
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from token.")

    # Calculate expiration time
    expires_in = result.get("expires_in", 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # Check if user already exists in DB
    db_token = db.query(Token).filter(Token.email == email).first()

    if db_token:
        # Update existing token
        db_token.access_token = result["access_token"]
        db_token.refresh_token = result.get("refresh_token")
        db_token.expires_at = expires_at
    else:
        # Create new token entry
        db_token = Token(
            email=email,
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_at=expires_at
        )
        db.add(db_token)
    
    db.commit()
    db.refresh(db_token)

    return {"message": f"Authentication successful for {email}!"}

# --- UPDATED HELPER FUNCTION WITH REFRESH LOGIC ---
def get_user_token(email: str, db: Session) -> str:
    if not email:
        raise HTTPException(status_code=401, detail="Email header missing")

    db_token = db.query(Token).filter(Token.email == email).first()
    if not db_token:
        raise HTTPException(status_code=404, detail="User not found or not authenticated. Please login.")

    # --- TOKEN REFRESH LOGIC ---
    if datetime.utcnow() > db_token.expires_at:
        print(f"Token for {email} has expired. Attempting to refresh.")
        if not db_token.refresh_token:
            raise HTTPException(status_code=401, detail="Token expired and no refresh token available. Please login again.")

        new_token_result = refresh_access_token(db_token.refresh_token)
        
        if "access_token" not in new_token_result:
            # If refresh fails, user must re-authenticate
            raise HTTPException(status_code=401, detail="Could not refresh token. Please login again.")

        # Update the database with the new token information
        db_token.access_token = new_token_result['access_token']
        # Some flows provide a new refresh token, some don't. Update if available.
        if 'refresh_token' in new_token_result:
            db_token.refresh_token = new_token_result['refresh_token']
        db_token.expires_at = datetime.utcnow() + timedelta(seconds=new_token_result['expires_in'])
        
        db.commit()
        print(f"Token for {email} refreshed successfully.")
        return db_token.access_token

    return db_token.access_token

# Helper to get a fresh token when needed
# def get_valid_access_token():
#     """
#     Retrieves a valid access token.
#     If the current token is expired or about to expire, it refreshes it.
#     Otherwise, it returns the existing token.
#     """
#     user_token = token_store.get("user")
#     if not user_token or "refresh_token" not in user_token:
#         raise HTTPException(status_code=401, detail="User not authenticated or no refresh token found.")

#     # Check if the token is expired or within the buffer period
#     if time.time() > user_token.get("expires_at", 0) - EXPIRATION_BUFFER_SECONDS:
#         print("Token expired or nearing expiration. Refreshing...")
#         refreshed_result = refresh_access_token(user_token["refresh_token"])
        
#         if "access_token" in refreshed_result:
#             # Update the entire token in the store with new values
#             new_expires_at = time.time() + refreshed_result["expires_in"]
#             user_token["access_token"] = refreshed_result["access_token"]
#             user_token["expires_at"] = new_expires_at
#             # Microsoft sometimes provides a new refresh token
#             user_token["refresh_token"] = refreshed_result.get("refresh_token", user_token["refresh_token"])
            
#             return user_token["access_token"]
#         else:
#             # If refresh fails, the user needs to log in again
#             print("ERROR: Could not refresh token.", refreshed_result.get("error_description"))
#             # Clear the invalid token from the store
#             token_store.clear()
#             raise HTTPException(status_code=401, detail="Could not refresh token. Please re-authenticate.")
#     else:
#         # Token is still valid, return it
#         print("Token is still valid.")
#         return user_token["access_token"]

@app.post("/event/create")
async def create_event_endpoint(event: EventRequest, email: str = Header(...), db: Session = Depends(get_db)):
    token = get_user_token(email, db)
    # The rest of your function remains the same...
    event_payload = {
        "subject": event.subject,
        "body": {"contentType": "HTML", "content": event.content or ""},
        "start": {"dateTime": event.start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": event.end_time, "timeZone": "Asia/Kolkata"},
        "isOnlineMeeting": event.is_online_meeting,
        "attendees": [{"emailAddress": {"address": att.email, "name": att.email}, "type": "required"} for att in event.attendees]
    }
    result = await create_event(token, event_payload)
    return result

@app.patch("/event/update/{event_id}")
async def update_event_endpoint(event_id: str, event: EventRequest, email: str = Header(...), db: Session = Depends(get_db)):
    token = get_user_token(email, db)
    # The rest of your function remains the same...
    update_payload = {
        "subject": event.subject,
        "body": {"contentType": "HTML", "content": event.content or ""},
        "start": {"dateTime": event.start_time, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": event.end_time, "timeZone": "Asia/Kolkata"}
    }
    result = await update_event(token, event_id, update_payload)
    return result

@app.delete("/event/delete/{event_id}")
async def delete_event_endpoint(event_id: str, email: str = Header(...), db: Session = Depends(get_db)):
    token = get_user_token(email, db)
    success = await delete_event(token, event_id)
    if success:
        return {"message": "Event deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete event")


@app.post("/logout")
def logout(email: str = Header(...), db: Session = Depends(get_db)):
    db_token = db.query(Token).filter(Token.email == email).first()
    if db_token:
        db.delete(db_token)
        db.commit()
        return JSONResponse({"message": f"Logged out successfully for {email}"})
    else:
        raise HTTPException(status_code=404, detail="User not found.")