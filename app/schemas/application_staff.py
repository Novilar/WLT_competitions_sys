# app/schemas/application_staff.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ApplicationStaffBase(BaseModel):
    full_name: str
    role: str
    contact_info: Optional[str] = None

class ApplicationStaffCreate(ApplicationStaffBase):
    pass

class ApplicationStaffOut(ApplicationStaffBase):
    id: UUID

    class Config:
        orm_mode = True
