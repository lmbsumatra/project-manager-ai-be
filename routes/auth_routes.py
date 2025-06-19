from fastapi import APIRouter, Depends, HTTPException
from schemas.user_schema import UserCreate, UserLogin, UserOut
from services.user_service import get_user_by_email, create_user, get_user_by_username
from core.auth import verify_password, create_access_token
from db.database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db, user.username, user.email, user.password)

# @router.post("/login")
# def login(user: UserLogin, db: Session = Depends(get_db)):
#     db_user = get_user_by_email(db, user.email)
#     if not db_user or not verify_password(user.password, db_user.password):
#         raise HTTPException(status_code=401, detail="Invalid credentials")
#     token = create_access_token({"sub": db_user.email})
#     return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
   
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    id = str(user.id)
    token = create_access_token({"sub": id})
    return {"access_token": token, "token_type": "bearer"}