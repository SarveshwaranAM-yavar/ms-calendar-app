# test_app.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from msal import ConfidentialClientApplication

# --- Configuration ---
load_dotenv()
CLIENT_ID = "7eef1cdf-2651-49e9-aabc-408e9c621d13"
CLIENT_SECRET = "jYL8Q~ZcLOpRaKuc6NyzfReADbhHenoNVkCmda1E"
REDIRECT_URI = "http://localhost:8000/callback"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["User.Read"] # Use minimal scope for testing

print("--- STARTING TEST APP ---")
print(f"CLIENT_ID: {CLIENT_ID}")
print(f"CLIENT_SECRET is {'SET' if CLIENT_SECRET else 'NOT SET'}")
print("-------------------------")

app = FastAPI()
msal_app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

# --- Endpoints ---
@app.get("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(code: str = None):
    if not code:
        raise HTTPException(400, "Missing auth code.")

    print("\n--- Received callback from Microsoft ---")
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    if "access_token" in result:
        print("--- SUCCESS: Token acquired! ---")
        return {"status": "success", "user": result.get("id_token_claims", {}).get("name")}
    else:
        print("\n!!! FAILURE: TOKEN ACQUISITION FAILED !!!")
        print("ERROR DETAILS:", result)
        raise HTTPException(500, detail=result)