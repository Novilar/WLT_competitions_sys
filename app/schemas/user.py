from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

# Схема для создания нового пользователя
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "athlete"   # позволим задать роль вручную для админа в MVP

# Схема для входа пользователя
class UserLogin(BaseModel):
    email_or_username: str
    password: str

# Схема для вывода информации о пользователе
class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    role: str

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }  # Для pydantic v2: позволяет инициализировать модель из объектов ORM


# Схема для токена авторизации
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
