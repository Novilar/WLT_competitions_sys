from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import Optional

class ApplicationAthleteBase(BaseModel):
    last_name: str = Field(..., example="Иванов")
    first_name: str = Field(..., example="Иван")
    middle_name: Optional[str] = Field(None, example="Иванович")
    gender: str  # "male" | "female" - можно заменить Literal
    birth_date: date
    weight_category: str
    entry_total: Optional[float] = None
    is_main: Optional[bool] = False

class ApplicationAthleteCreate(ApplicationAthleteBase):
    pass

class ApplicationAthleteOut(ApplicationAthleteBase):
    id: UUID

    class Config:
        orm_mode = True
