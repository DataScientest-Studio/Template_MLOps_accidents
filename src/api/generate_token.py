import jwt
import datetime

# Replace with the same secret key used in your service.py
SECRET_KEY = "I_know_that_this _is_unsecure_but_I_don't_care"

# Function to generate a JWT token
def generate_jwt():
    payload = {
        "sub": "user_id_123",  # Subject (e.g., user ID or username)
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1),  # Expiration time
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# Generate and print the token
if __name__ == "__main__":
    token = generate_jwt()
    print(f"Your JWT Token: {token}")