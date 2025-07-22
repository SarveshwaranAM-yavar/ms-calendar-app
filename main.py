from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse
from auth import get_auth_url, get_token_by_auth_code, refresh_access_token
from graph_api import create_event, update_event, delete_event
from models import EventRequest
from typing import Optional

app = FastAPI()
token_store = {}  # In production, use a DB or encrypted store

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
    if not code:
        raise HTTPException(status_code=400, detail="Missing auth code")
    print("Authorization code : 1111111111111",code)
    result = get_token_by_auth_code(code)
    if "access_token" in result:
        token_store["user"] = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),  # NEW
            "expires_in": result["expires_in"],
        }
        print("token store: 11111111111111111",token_store)
        return {"message": "Authentication successful!"}
    else:
        raise HTTPException(status_code=400, detail="Authentication failed")

# Helper to get a fresh token when needed
def get_valid_access_token():
    user_token = token_store.get("user")
    if not user_token:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # In production, check for token expiry instead of always refreshing
    refreshed = refresh_access_token(user_token["refresh_token"])
    if "access_token" in refreshed:
        user_token["access_token"] = refreshed["access_token"]
        user_token["refresh_token"] = refreshed.get("refresh_token", user_token["refresh_token"])
        return user_token["access_token"]
    raise HTTPException(status_code=401, detail="Failed to refresh token")

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
def logout():
    token_store.pop("user", None)
    return JSONResponse({"message": "Logged out successfully"})