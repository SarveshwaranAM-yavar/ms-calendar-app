import time
from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse
from app.auth import get_auth_url, get_token_by_auth_code, refresh_access_token
from app.graph_api import create_event, update_event, delete_event
from app.models import EventRequest
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
token_store = {}
  # In production, use a DB or encrypted store
EXPIRATION_BUFFER_SECONDS = 300
# Define allowed origins
origins = [
    "http://localhost:8000",  # React frontend local dev
    "http://127.1.77.6:8000",
    "*" , # Add production frontend domain here
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # or ["*"] for public APIs (not recommended for prod)
    allow_credentials=True,
    allow_methods=["*"],              # or specify: ["GET", "POST", "PUT", ...]
    allow_headers=["*"],              # or specify: ["Authorization", "Content-Type"]
)


@app.get("/")
def root():
    return {"message": "Microsoft Calendar Integration using FastAPI"}

@app.get("/auth/login")
def login():
    token_store.clear() 
    auth_url = get_auth_url()
    print("3333333333",auth_url)
    return RedirectResponse(auth_url)

@app.get("/callback")
def auth_callback(code: Optional[str] = None):
    """
    Handles the callback from Microsoft after user authentication.
    Exchanges the authorization code for an access token and refresh token.
    """
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # Assuming get_token_by_auth_code is a wrapper around MSAL's acquire_token_by_auth_code_flow
    result = get_token_by_auth_code(code) 
    
    if "access_token" in result:
        # Calculate the absolute expiration time (current time + duration)
        expires_at = time.time() + result["expires_in"]
        
        token_store["user"] = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_at": expires_at,  # Store the calculated timestamp
        }
        return {"message": "Authentication successful!"}
    else:
        # Log the error from Microsoft for debugging
        print("Authentication failed:", result.get("error_description"))
        raise HTTPException(status_code=400, detail="Authentication failed")

# Helper to get a fresh token when needed
def get_valid_access_token():
    """
    Retrieves a valid access token.
    If the current token is expired or about to expire, it refreshes it.
    Otherwise, it returns the existing token.
    """
    user_token = token_store.get("user")
    if not user_token or "refresh_token" not in user_token:
        raise HTTPException(status_code=401, detail="User not authenticated or no refresh token found.")

    # Check if the token is expired or within the buffer period
    if time.time() > user_token.get("expires_at", 0) - EXPIRATION_BUFFER_SECONDS:
        print("Token expired or nearing expiration. Refreshing...")
        refreshed_result = refresh_access_token(user_token["refresh_token"])
        
        if "access_token" in refreshed_result:
            # Update the entire token in the store with new values
            new_expires_at = time.time() + refreshed_result["expires_in"]
            user_token["access_token"] = refreshed_result["access_token"]
            user_token["expires_at"] = new_expires_at
            # Microsoft sometimes provides a new refresh token
            user_token["refresh_token"] = refreshed_result.get("refresh_token", user_token["refresh_token"])
            
            return user_token["access_token"]
        else:
            # If refresh fails, the user needs to log in again
            print("ERROR: Could not refresh token.", refreshed_result.get("error_description"))
            # Clear the invalid token from the store
            token_store.clear()
            raise HTTPException(status_code=401, detail="Could not refresh token. Please re-authenticate.")
    else:
        # Token is still valid, return it
        print("Token is still valid.")
        return user_token["access_token"]

@app.post("/event/create")
async def create_event_endpoint(event: EventRequest):
    token = token_store.get("user", {}).get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated")

    event_payload = {
        "subject": event.subject,
        "body": {
            "contentType": "HTML",
            "content": event.content or ""
        },
        "start": {
            "dateTime": event.start_time,
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": event.end_time,
            "timeZone": "Asia/Kolkata"
        },
        "isOnlineMeeting": event.is_online_meeting,
        "attendees": [
            {
                "emailAddress": {"address": att.email, "name": att.email},
                "type": "required"
            } for att in event.attendees
        ]
    }

    result = await create_event(token, event_payload)
    return result

@app.patch("/event/update/{event_id}")
async def update_event_endpoint(event_id: str, event: EventRequest):
    token = token_store.get("user", {}).get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated")

    update_payload = {
        "subject": event.subject,
        "body": {
            "contentType": "HTML",
            "content": event.content or ""
        },
        "start": {
            "dateTime": event.start_time,
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": event.end_time,
            "timeZone": "Asia/Kolkata"
        }
    }

    result = await update_event(token, event_id, update_payload)
    return result

@app.delete("/event/delete/{event_id}")
async def delete_event_endpoint(event_id: str):
    token = token_store.get("user", {}).get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="User not authenticated")

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
