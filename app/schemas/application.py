# app/schemas/application.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from .application_athlete import ApplicationAthleteCreate, ApplicationAthleteOut
from .application_staff import ApplicationStaffCreate, ApplicationStaffOut
from app.models.enums import ApplicationStatus, ApplicationType


class ApplicationBase(BaseModel):
    federation_name: Optional[str] = None
    type: str = "preliminary"

class ApplicationCreate(ApplicationBase):
    athletes: List[ApplicationAthleteCreate]
    staff: List[ApplicationStaffCreate] = []


class ApplicationUpdate(ApplicationBase):
    athletes: List[ApplicationAthleteCreate]


class ApplicationEventOut(BaseModel):
    id: UUID
    action: str
    comment: str | None
    timestamp: datetime
    user_id: UUID | None

    class Config:
        orm_mode = True


class ApplicationTransitionIn(BaseModel):
    action: str
    comment: str | None = None

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    comment: Optional[str] = None
    action: Optional[str] = None


class ApplicationOut(ApplicationBase):
    id: UUID
    competition_id: UUID
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[datetime] = None
    last_comment: Optional[str] = None
    last_action: Optional[str] = None

    # Для фронта: поле, которое раньше использовалось — submission_date
    submission_date: Optional[datetime] = None

    athletes: List[ApplicationAthleteOut] = []
    staff: List[ApplicationStaffOut] = []
    events: list[ApplicationEventOut] = []
    federation_name: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True



class ApplicationListItemOut(BaseModel):
    id: UUID
    type: ApplicationType
    status: ApplicationStatus

    federation_id: UUID
    federation_name: str | None

    submission_date: Optional[datetime]  # 🔥 ВАЖНО
    submitted_by: Optional[UUID]          # 🔥 тоже Optional

    male_count: int
    female_count: int

    class Config:
        orm_mode = True

