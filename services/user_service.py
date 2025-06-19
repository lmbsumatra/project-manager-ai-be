from sqlalchemy.orm import Session
from models.user_model import User
from core.auth import hash_password

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, username: str, email: str, password: str):
    user = User(username=username, email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
