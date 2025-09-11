# Импортируем стандартные библиотеки для работы с датой и временем, UUID
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

# JOSE — библиотека для работы с JWT
from jose import jwt, JWTError

# FastAPI зависимости и исключения
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# SQLAlchemy сессия
from sqlalchemy.orm import Session

# Конфигурация проекта (секретный ключ, время жизни токена)
from app.config import settings
from app.database import get_db
from app.models.user import User

# Настраиваем схему безопасности HTTP Bearer (токен передается в заголовке Authorization)
security_scheme = HTTPBearer()
ALGORITHM = "HS256"

# Функция создания JWT-токена
def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()     # Копируем данные, чтобы не изменить оригинал
    expire = datetime.utcnow() + timedelta(    # Вычисляем время истечения токена
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)     # Возвращаем закодированный JWT-токен

# Функция получения текущего пользователя из токена
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    # Настраиваем стандартное исключение для недействительного токе
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise cred_exc
        # sub у нас — строковый UUID
        user_id = UUID(sub)
    except (JWTError, ValueError):
        raise cred_exc

    # Получаем пользователя из базы по его UUID
    user = db.get(User, user_id)
    if not user:
        raise cred_exc
    return user
