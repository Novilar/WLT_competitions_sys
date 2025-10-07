from pydantic import BaseModel
from typing import Optional
from enum import Enum
from uuid import UUID

class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ApplicationBase(BaseModel):
    competition_id: UUID
    status: Optional[ApplicationStatus] = ApplicationStatus.pending
    profile: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationOut(ApplicationBase):
    id: UUID
    user_id: UUID

    class Config:
        orm_mode = True
