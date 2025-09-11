from pydantic import BaseModel
from uuid import UUID


# Модель базы для жеребьевки
class DrawResult(BaseModel):
    user_id: UUID
    number: int
    # Для настройки поведения Pydantic модели.
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }
