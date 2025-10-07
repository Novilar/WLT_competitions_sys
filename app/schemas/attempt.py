from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.models.attempt import LiftType


class AttemptCreate(BaseModel):
    athlete_name: str
    weight: int
    lift_type: LiftType


class AttemptOut(BaseModel):
    id: UUID
    competition_id: UUID
    athlete_name: str
    weight: int
    lift_type: LiftType
    status: str
    result: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
