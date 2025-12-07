from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import Optional

class ApplicationAthleteBase(BaseModel):
    last_name: str = Field(..., example="Иванов")
    first_name: str = Field(..., example="Иван")
    middle_name: Optional[str] = Field(None, example="Иванович")
    gender: str
    birth_date: date
    weight_category: str
    entry_total: Optional[float] = None
    is_main: Optional[bool] = False

class ApplicationAthleteCreate(ApplicationAthleteBase):
    pass

class ApplicationAthleteOut(BaseModel):
    id: UUID
    gender: str
    birth_date: date
    weight_category: str
    entry_total: Optional[float] = None
    is_main: Optional[bool] = False

    # 🔥 виртуальные поля
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None

    class Config:
        orm_mode = True

    @staticmethod
    def from_orm(model):
        # model.full_name существует в ORM
        full = (model.full_name or "").split()

        last = full[0] if len(full) > 0 else None
        first = full[1] if len(full) > 1 else None
        middle = " ".join(full[2:]) if len(full) > 2 else None

        return ApplicationAthleteOut(
            id=model.id,
            gender=model.gender.value if hasattr(model.gender, "value") else model.gender,
            birth_date=model.birth_date,
            weight_category=model.weight_category,
            entry_total=model.entry_total,
            is_main=model.is_main,
            last_name=last,
            first_name=first,
            middle_name=middle,
        )

