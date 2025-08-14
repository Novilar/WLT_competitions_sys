from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from app import schemas, models
from app.database import get_db
from app.core.security import create_access_token
from typing import Dict

router = APIRouter()

@router.post("/register", response_model=schemas.user.UserOut)
def register(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.user.User).filter(models.user.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = bcrypt.hash(user.password)
    db_user = models.user.User(email=user.email, hashed_password=hashed_pw, full_name=user.full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(user: schemas.user.UserLogin, db: Session = Depends(get_db)) -> Dict[str, str]:
    db_user = db.query(models.user.User).filter(models.user.User.email == user.email).first()
    if not db_user or not bcrypt.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer"}
