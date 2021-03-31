import time
from typing import Dict
import jwt

JWT_SECRET = 'please_please_update_me_please'
JWT_ALGORITHM = 'HS256'


def token_response(token: str):
    return {
        'access_token': token
    }


def generate_jwt(email: str):
    payload = {
        "email": email,
        "expires": time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token
