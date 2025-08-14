from pydantic import BaseModel
from typing import Any

class ApplicationCreate(BaseModel):
    competition_id: int
    profile: Any  # Можно dict, но для упрощения Any

class ApplicationOut(BaseModel):
    id: int
    competition_id: int
    user_id: int
    status: str
    profile: Any

    class Config:
        orm_mode = True
