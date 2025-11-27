from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from .application_athlete import ApplicationAthleteCreate, ApplicationAthleteOut
from .application_staff import ApplicationStaffCreate, ApplicationStaffOut

class ApplicationBase(BaseModel):
    federation_name: Optional[str] = None
    type: str = "preliminary"

class ApplicationCreate(ApplicationBase):
    athletes: List[ApplicationAthleteCreate]
    staff: List[ApplicationStaffCreate]

class ApplicationUpdate(ApplicationBase):
    athletes: List[ApplicationAthleteCreate]

class ApplicationOut(ApplicationBase):
    id: UUID
    competition_id: UUID
    submitted_by: UUID
    submitted_at: datetime
    athletes: List[ApplicationAthleteOut]
    staff: List[ApplicationStaffOut]

    class Config:
        orm_mode = True
