import os
from dotenv import load_dotenv

load_dotenv()

# CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CLIENT_ID="7eef1cdf-2651-49e9-aabc-408e9c621d13"
CLIENT_SECRET="jYL8Q~ZcLOpRaKuc6NyzfReADbhHenoNVkCmda1E"

# TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/common"
# REDIRECT_URI = os.getenv("REDIRECT_URI")
REDIRECT_URI="http://localhost:8000/callback"
SCOPES = ["Calendars.ReadWrite", "User.Read"]
#"Calendars.ReadWrite"
#Onlinemeetigns.ReadWrite
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

DATABASE_URL = "postgresql://sarveshwaranam:421300@localhost:5432/ms_calendar_access"


print("CLIENT_ID = ", CLIENT_ID)
print("CLIENT_SECRET = ", CLIENT_SECRET)