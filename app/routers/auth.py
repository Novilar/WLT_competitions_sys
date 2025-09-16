from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app import schemas, models
from app.database import get_db
from app.core.security import create_access_token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Функция для хэширования пароля
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Функция для проверки пароля
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# Регистрация пользователя
@router.post("/register", response_model=schemas.user.UserOut, status_code=201)
def register(user: schemas.user.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.user.User).filter(models.user.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = models.user.User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
        global_role=user.role or "athlete",  # сохраняем в global_role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# Вход
@router.post("/login", response_model=schemas.user.Token)
def login(user: schemas.user.UserLogin, db: Session = Depends(get_db)):
    db_user = (
        db.query(models.user.User)
        .filter(
            (models.user.User.email == user.email_or_username) |
            (models.user.User.full_name == user.email_or_username)
        )
        .first()
    )
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user.id), "role": db_user.global_role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": db_user.full_name,
        "role": db_user.global_role
    }
