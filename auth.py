from msal import ConfidentialClientApplication
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, AUTHORITY, SCOPES,REDIRECT_URI

app = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,  
        "response_mode": "query",
        "scope": "User.Read Calendars.ReadWrite offline_access",
        "prompt": "select_account"
        #  "prompt": "login",  # force login every time
        # "login_hint": "xyz@example.com",
    }
    print("111111111111111",CLIENT_ID)
    print("2222222222222222",CLIENT_SECRET)
    return f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urlencode(params)}"

def get_token_by_auth_code(code: str):
    result = app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    if "access_token" not in result:
        print("ERROR IN TOKEN RESPONSE:", result)  # 👈 Add this
    return result



def refresh_access_token(refresh_token: str):
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
    if "access_token" not in result:
        print("ERROR IN REFRESH:", result)
    return result