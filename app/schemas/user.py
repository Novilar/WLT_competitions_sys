from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.schemas.roles import GlobalRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: Optional[GlobalRole] = GlobalRole.athlete   # используем Enum


class UserLogin(BaseModel):
    email_or_username: str
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    global_role: GlobalRole   # теперь строго Enum

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: Optional[str] = None
    role: Optional[GlobalRole] = None
