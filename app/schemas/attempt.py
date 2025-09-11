from pydantic import BaseModel
from uuid import UUID


# Модель для создания новой попытки на соревновании
class AttemptCreate(BaseModel):
    competition_id: UUID
    weight: int
    result: str  # "success" or "fail"

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Модель для вывода информации о попытке
class AttemptOut(BaseModel):
    id: UUID
    competition_id: UUID
    user_id: UUID
    weight: int
    result: str

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }
