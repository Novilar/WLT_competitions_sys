from pydantic import BaseModel
from uuid import UUID
from datetime import date

# Базовая модель соревнования
class CompetitionBase(BaseModel):
    name: str
    date: date
    location: str


# Модель для создания нового соревнования
class CompetitionCreate(CompetitionBase):
    pass


# Модель для вывода информации о соревновании
class CompetitionOut(CompetitionBase):
    id: UUID

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }  # заменяет orm_mode в Pydantic v2
