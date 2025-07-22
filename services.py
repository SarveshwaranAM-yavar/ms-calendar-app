import jwt
# --- Helper function to decode JWT and get email ---
def get_email_from_id_token(id_token: str) -> str:
    try:
        # Decode without verification to get claims
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        return decoded_token.get("preferred_username") # Or 'email' depending on the token
    except jwt.PyJWTError as e:
        print(f"Error decoding token: {e}")
        return None