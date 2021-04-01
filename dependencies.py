import token

from fastapi import Header, HTTPException, Depends
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy.testing import db

import crud
from connection.db_connection import get_db
from security.jwt_util import SECRET_KEY, ALGORITHM, verify_password

#
# async def get_token_header(x_token: str = Header(...)):
#     if x_token != "fake-super-secret-token":
#         raise HTTPException(status_code=400, detail="X-Token header invalid")
#
#     token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGdtYWlsLmNvbSIsImV4cCI6MTYxNzI3MjE5Mn0.uqzRWRC3szgMbvW6bROsVAUWdAut1krDCwjEgGbnK1Y'
#     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#     username: str = payload.get("sub")
#
#     print(username)
#
#
# async def get_query_token(token: str):
#     if token != "jessica":
#         raise HTTPException(status_code=400, detail="No Jessica token provided")


async def authenticate(token: str = Header(...), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")

    print(username)
    user_dict = crud.get_user_by_email(db, email=username)
    if not user_dict:
        return False
    print(user_dict)
