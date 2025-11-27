from pydantic import BaseModel
from uuid import UUID

class ApplicationStaffBase(BaseModel):
    full_name: str
    role: str
    contact_info: str | None = None

class ApplicationStaffCreate(ApplicationStaffBase):
    pass

class ApplicationStaffOut(ApplicationStaffBase):
    id: UUID

    class Config:
        from_attributes = True
