from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from config.route import Route
from connection.db_connection import get_db
from models.schemas import schemas
from security.jwt_util import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user2

router = APIRouter()


@router.post("/user/token")
def find_user_by_token(token: schemas.UserPutToken, db: Session = Depends(get_db)):
    user = get_current_user2(token=token.access_token, db=db)
    print(user.email)
    return user


@router.post(Route.V1.LOGIN)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_dict = authenticate_user(form_data.username, form_data.password, db)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
