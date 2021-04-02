from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.entity import models
from models.schemas import schemas
from security.jwt_util import get_current_user2

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    # fake_hashed_password = user.password + "notreallyhashed"
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_token(db: Session, user: schemas.UserPutToken):
    access_token = user.access_token
    user = get_current_user2(access_token)
    db_user = models.User(id=user['id'], access_token=access_token)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
