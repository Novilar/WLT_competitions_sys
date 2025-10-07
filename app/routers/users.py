# app/routers/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=list[schemas.user.UserOut])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(models.user.User).all()
