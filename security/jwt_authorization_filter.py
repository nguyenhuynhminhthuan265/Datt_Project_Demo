from fastapi import Header, Depends
from jose import jwt
from sqlalchemy.orm import Session

import crud
from connection.db_connection import get_db
from security.jwt_util import SECRET_KEY, ALGORITHM


async def authenticate(authorization_header: str = Header(...), db: Session = Depends(get_db)):
    access_token = authorization_header.replace('Bearer ','')
    payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get("sub")

    print(username)
    user_dict = crud.get_user_by_email(db, email=username)
    if not user_dict:
        return False
    print(user_dict)
