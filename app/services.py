import jwt
# --- UPDATED HELPER FUNCTION ---
def get_email_from_id_token(id_token: str) -> str:
    """
    Decodes the id_token and retrieves the user's email, checking multiple
    possible claims.
    """
    if not id_token:
        print("ID token is missing.")
        return None
        
    try:
        # Decode without verification to get claims
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        
        # Check for email in common claims
        email = decoded_token.get("preferred_username")  # For most work/school accounts
        if not email:
            email = decoded_token.get("email") # For some personal and work accounts
        if not email:
            email = decoded_token.get("upn") # User Principal Name
            
        return email

    except Exception as e:
        print(f"Error decoding token: {e}")
        return None