from pydantic import BaseModel
from typing import Optional
from enum import Enum
from uuid import UUID


class LiftType(str, Enum):
    snatch = "snatch"   # рывок
    clean_jerk = "clean_jerk"  # толчок


class AttemptBase(BaseModel):
    weight: float
    lift_type: LiftType


class AttemptCreate(AttemptBase):
    athlete_id: UUID  # участник, которому принадлежит попытка


class AttemptOut(AttemptBase):
    id: UUID
    user_id: UUID
    athlete_id: UUID
    athlete_name: Optional[str] = None
    competition_id: UUID
    result: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True
