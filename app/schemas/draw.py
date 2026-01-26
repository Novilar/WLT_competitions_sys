from pydantic import BaseModel
from uuid import UUID
from typing import Optional



class DrawAthleteOut(BaseModel):
    athlete_id: UUID
    last_name: str
    first_name: str
    gender: str
    weight_category: str
    entry_total: Optional[int]
    group_letter: str
    lot_number: int

    class Config:
        from_attributes = True


class DrawGroupOut(BaseModel):
    gender: str
    weight_category: str
    group_letter: str
    athletes: list[DrawAthleteOut]


class DrawResultOut(BaseModel):
    competition_id: UUID
    groups: list[DrawGroupOut]
