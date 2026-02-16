from pydantic import BaseModel
from uuid import UUID
from enum import Enum
from typing import Optional


class LiftType(str, Enum):
    snatch = "snatch"
    clean_and_jerk = "clean_and_jerk"


class DrawEntryOut(BaseModel):
    id: UUID
    athlete_id: UUID
    gender: str
    weight_category: str
    group_letter: str
    lot_number: int

    class Config:
        from_attributes = True

class AttemptCreate(BaseModel):
    competition_id: UUID
    draw_entry_id: UUID     # 👈 вместо athlete_id
    weight: int
    lift_type: LiftType


class AttemptOut(BaseModel):
    id: UUID
    draw_entry_id: UUID
    competition_id: UUID
    weight: int
    lift_type: LiftType
    status: str
    result: Optional[str]

    class Config:
        from_attributes = True

