from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class ApplicationCreate(BaseModel):
    competition_id: UUID
    status: str
    profile: str



class ApplicationOut(BaseModel):
    id: UUID
    competition_id: UUID
    user_id: UUID
    status: str
    profile: str

    model_config = {
        "from_attributes": True
    }
